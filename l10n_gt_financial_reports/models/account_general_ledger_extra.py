# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .account_general_ledger import AccountGeneralLedgerReport as GLedger
import re
import copy
from odoo.osv import expression
from datetime import datetime



import logging

_logger = logging.getLogger( __name__ )

class AccountGeneralLedgerReportExtra(models.AbstractModel):
    _inherit = "account.general.ledger"

    @api.model
    def _get_lines(self, options, line_id=None):
        with_hierarchy = options.get("hierarchy", False)
        unfold_all = options.get("unfold_all", False)

        if with_hierarchy and unfold_all and not line_id:
            # Esto me retorna los grupos sin padres, los del primer nivel
            res = GLedger._get_lines(self, options, line_id)

            counter = 0

            child = False
            if res:
                child = res[counter]

            while child:
                holder_id = str(child["id"])

                # Para la generacion del pdf me interesa que se llame este metodo solo con las cuentas,
                # y sin los asientos, esto porque otro metodo se encargara de llamar la funcion par que retorne todas las lineas
                # esto con el fin de poder hacer la generacion de pdf un poco mas rapida

                no_moves = self._context.get("no_moves", False)

                if ("account_" in holder_id and not no_moves) or "__group_" in holder_id:
                    add_lines = GLedger._get_lines(self, options, child["id"])

                    if len(add_lines) > 1:
                        child["unfolded"] = True

                    if add_lines:
                        target = counter + 1
                        res[target:target] = add_lines[1:]

                counter += 1
                if counter < len(res):
                    child = res[counter]
                else:
                    child = False
        else:
            res = GLedger._get_lines(self, options, line_id)

        return res

    def get_account_parents(self, account_id, formatted=True):
        parents = []
        account = self.env["account.account"].browse(account_id)
        if account:
            group = account.group_id
            while group:
                parents.append(group.id)
                group = group.parent_id if group.parent_id else False

        if formatted:
            for x in range(0, len(parents)):
                holder = "__group_{0}".format(parents[x])
                parents[x] = holder

        return parents

    def get_month_number(self):
        month_number = {"ene.": "01", "feb.": "02", "mar.": "03", "abr.": "04", "may.": "05", "jun.": "06",
                        "jul.": "07", "ago.": "08", "sept.": "09", "oct.": "10", "nov.": "11", "dic.": "12"}
        return month_number

    def format_date(self, date):
        parts = date.split()
        month_number = self.get_month_number()
        target_month = month_number[parts[1]]
        holder = "{0}-{1}-{2}".format(parts[2], target_month, parts[0])
        obj_date = datetime.strptime(holder, "%Y-%m-%d")
        return obj_date

    def get_init_bal(self, target_date, acc_id, day_domain):
        day_domain += [("date", "<", target_date)]
        day_domain += [("account_id", "=", acc_id)]
        init_bal = self.env["account.move.line"].read_group(day_domain, ["account_id", "credit", "debit","date"],
                                                            ["account_id"], orderby="date asc")
        result = 0
        if init_bal:
            holder = init_bal[0]
            holder_bal = holder["debit"] - holder["credit"]
            result = holder_bal

        return result

    def get_pdf_data(self, options):
        # print_mode True es para que retorne todas las lineas
        options["hierarchy"] = True
        options["unfold_all"] = True
        date_from = options["date"]["date_from"]
        date_to = options["date"]["date_to"]
        aml_domain = []

        ana_acc = options.get("analytic_accounts", [])
        if ana_acc:
            analytic_ids = [int(r) for r in options['analytic_accounts']]
            aml_domain = expression.AND([aml_domain, [('analytic_account_id', 'in', analytic_ids)]])

        if options.get('journals'):
            journal_ids = [j.get('id') for j in options.get('journals') if j.get('selected')]
            if journal_ids:
                aml_domain = expression.AND([aml_domain, [('journal_id', 'in', journal_ids)]])

        if not options.get('all_entries'):
            aml_domain = expression.AND([aml_domain, [('parent_state', '=', "posted")]])

        expr = self.get_clean_expr()
        # El resultado de este serian solo grupos y dentro de ellos las cuentas sin asientos
        lines = self.with_context({'print_mode': True, 'no_moves': True})._get_lines(options, line_id=None)

        counter = 0
        account_totals = {}
        is_daily_book = self._context.get("is_daily_book", False)
        for line in lines:
            # ya son cuatro columnas, la primera no tiene nada, de forma que esa uso para el saldo inicial
            val_cols = [0]
            if "vals_cols" not in line:
                for col in line["columns"]:
                    clean = 0
                    val_cols.append(clean)

                line["vals_cols"] = val_cols

            # De las cuentas he de recuperar el resumen por dia
            if "account_" in line["id"]:
                acc_id = int(line["id"][8:])
                lines_domain = copy.deepcopy(aml_domain)
                lines_domain += [("date", ">=", date_from), ("date", "<=", date_to)]
                lines_domain += [("account_id", "=", acc_id)]
                if is_daily_book:
                    res = self.env["account.move.line"].read_group(lines_domain, ["move_id", "move_name", "date", "credit", "debit",],
                                                                   ["move_id", "move_name", "date:day"],
                                                                   orderby="date asc")
                else:
                    res = self.env["account.move.line"].read_group(lines_domain, ["date", "credit", "debit"],
                                                                   ["date:day"],
                                                                   orderby="date asc")

                target_pos = counter + 1
                day_counter = 0

                # holder_bal tendra el saldo inicial
                day_bal = 0
                move_bal = 0

                to_add = []
                acc_totals = [0] * 4
                day_level = line["level"] + 1
                last_day = len(res) - 1

                move_counter = 0
                if is_daily_book:
                    for move in res:
                        date_holder = move["date"]
                        target_date = date_holder.strftime("%Y-%m-%d")
                        formatted_date = date_holder.strftime("%d/%m/%Y")
                        target_name = str(move["move_id"][1])

                        holder_bal = 0
                        if move_counter == 0:
                            move_domain = copy.deepcopy(aml_domain)
                            holder_bal = self.get_init_bal(target_date, acc_id, move_domain)
                            acc_totals[0] = holder_bal
                        else:
                            # Caso contrario el saldo inicial es el saldo final en move_bal que en este punto aun no ha cambiado con respecto
                            # al anterior
                            holder_bal = move_bal

                        new_id = "move_{0}_{1}".format(acc_id, move["move_id"])
                        move_bal = holder_bal + move["debit"] - move["credit"]

                        # Deberia establecerle el padre y el nivel
                        new_line = {"id": new_id, "name": target_name, "date": formatted_date,
                                    "vals_cols": [holder_bal, move["debit"], move["credit"], move_bal],
                                    "parent_id": line["id"], "level": day_level}

                        to_add.append(new_line)

                        acc_totals[1] += move["debit"]
                        acc_totals[2] += move["credit"]

                        if move_counter == last_day:
                            acc_totals[3] = move_bal

                        move_counter += 1
                else:
                    for day in res:
                        date_holder = self.format_date(day["date:day"])
                        target_date = date_holder.strftime("%Y-%m-%d")
                        target_name = date_holder.strftime("%d/%m/%Y")

                        holder_bal = 0
                        if day_counter == 0:
                            day_domain = copy.deepcopy(aml_domain)
                            holder_bal = self.get_init_bal(target_date, acc_id, day_domain)
                            acc_totals[0] = holder_bal
                        else:
                            # Caso contrario el saldo inicial es el saldo final en day_bal que en este punto aun no ha cambiado con respecto
                            # al anterior
                            holder_bal = day_bal

                        new_id = "date_{0}_{1}".format(acc_id, target_date)
                        day_bal = holder_bal + day["debit"] - day["credit"]

                        # Deberia establecerle el padre y el nivel
                        new_line = {"id": new_id, "name": target_name,
                                    "vals_cols": [holder_bal, day["debit"], day["credit"], day_bal],
                                    "parent_id": line["id"], "level": day_level}

                        to_add.append(new_line)

                        acc_totals[1] += day["debit"]
                        acc_totals[2] += day["credit"]

                        if day_counter == last_day:
                            acc_totals[3] = day_bal

                        day_counter += 1

                # Aun si no tiene dias en el periodo se ha de colocar su saldo inicial para esto se hace la consulta
                if not res:
                    day_domain = copy.deepcopy(aml_domain)
                    holder_bal = self.get_init_bal(date_from, acc_id, day_domain)
                    acc_totals[0] = holder_bal
                    acc_totals[3] = holder_bal

                # Genera una linea de totales
                total_id = "total_{0}".format(acc_id)
                total_name = "Total de {0}".format(line["name"])
                new_line = {"id": total_id, "name": total_name, "vals_cols": acc_totals, "parent_id": line["id"],
                            "level": day_level}

                to_add.append(new_line)

                lines[target_pos:target_pos] = to_add
                # Determino que grupos se veran afectados por los totales de esa cuenta

                parents = self.get_account_parents(acc_id)
                account_totals[acc_id] = {"parents": parents, "totals": acc_totals}

            counter += 1

        # Por cada linea que sea un grupo he de verificar si le tengo que sumar los valores de algun cuenta,
        # ya sea porque la cuenta lo tiene como grupo, o el grupo de la cuenta es hijo del grupo
        # actual
        section_lines = list(filter(lambda d: "__group_" in str(d['id']), lines))

        for line in section_lines:
            acc_lines = list(filter(lambda d: line["id"] in account_totals[d]["parents"], account_totals))
            for acc_id in acc_lines:
                totals = account_totals[acc_id]["totals"]
                for x in range(0, len(totals)):
                    line["vals_cols"][x] += totals[x]

        return lines

    def _get_reports_buttons(self):
        res = super(AccountGeneralLedgerReportExtra, self)._get_reports_buttons()
        res.append({"name": "Libro Mayor", "action": "daily_mayor_book_pdf", "sequence": 6})
        return res

    def mayor_book_pdf(self, options):
        report = self.env.ref("l10n_gt_financial_reports.daily_general_ledger_report")
        context = self.env.context
        data = self.get_pdf_data(options)
        holder = self.env["account.move"].search([], limit=1)
        date_from = options["date"]["date_from"]
        date_to = options["date"]["date_to"]
        date_format = "%d/%m/%Y"
        holder_from = datetime.strptime(date_from, "%Y-%m-%d").strftime(date_format)
        holder_to = datetime.strptime(date_to, "%Y-%m-%d").strftime(date_format)
        to_data = {"data": data, "docids": holder.id, "date_from": holder_from, "date_to": holder_to,'folio':context.get('folio',False)}
        return report.report_action(holder, data=to_data)

    def daily_mayor_book_pdf(self, options):
        view_id = self.env['ir.model.data'].xmlid_to_res_id('l10n_gt_financial_reports.wizard_folio_general_legder')
        return {
            'type': 'ir.actions.act_window',
            'name': _("Folio Libro Mayor"),
            'view_mode': 'form',
            'res_model': 'wizard.folio.general.ledger',
            'views': [[view_id, 'form']],
            'target': 'new',
            'context': {
                'default_options': options,
            }
        }
