# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re


import logging

_logger = logging.getLogger( __name__ )

class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.general.ledger"

    filter_hierarchy = False

    def get_first_group(self, group, target="group"):
        result = False
        level = 1
        if not group.parent_id:
            result = group
        else:
            parent = group.parent_id
            result = group.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
                if parent:
                    result = parent

        if target == "group":
            return result
        else:
            return level

    def get_account_group(self, acc):
        holder = acc["id"].replace("account_", "")
        acc_id = int(holder)
        account = self.env["account.account"].browse(acc_id)
        res = account.group_id
        return res

    def get_direct_childs(self, group_id):
        groups = self.env["account.group"].search([["parent_id", "=", group_id]])
        return groups

    def get_all_childs(self, group_id):
        groups = self.env["account.group"].search([["parent_id", "=", group_id]])
        all_childs = groups.ids

        group = False
        if groups:
            group = groups[0]

        while group:
            holder = self.env["account.group"].search([["parent_id", "=", group.id]])
            all_childs += holder.ids
            groups += holder
            groups -= group
            if groups:
                group = groups[0]
            else:
                group = False

        return all_childs

    def get_clean_expr(self):
        lang = self.env["res.lang"].search([["code", "=", self.env.user.lang]], limit=1)
        expr = r'[^0-9-' + lang.decimal_point + r']+'
        return expr

    def clean_value(self, value, expr):
        #_logger.info("*******************Value/Expr*******************")
        #_logger.info(value)
        #_logger.info(expr)
        clean = re.sub(expr, '', str(value))
        #_logger.info('*******************clean*******************')
        #_logger.info(clean)
        holder = float(clean or 0.00)
        return holder

    @api.model
    def _get_lines(self, options, line_id=None):
        with_hierarchy = options.get("hierarchy", False)

        #Para que no me de error la llamada original es que uso __group_, para que tenga ocho caracteres y el codigo original no de error
        #en la llamda a super, porque aparentemente las lineas desplegadas se guardan en la sesion y al nomas entrar se ejecuta codigo
        #involucrando dichas lineas
        group_line_id = False
        group_line = False
        direct_childs = []
        group_level = 1
        holder_group = False
        if with_hierarchy and line_id:
            #Cuando se haya desplegado un grupo he de llamar a la funcion original
            if "__group_" in line_id:
                group_line = line_id
                holder = line_id.replace("__group_", "")
                group_line_id = int(holder)
                direct_childs = self.get_direct_childs(group_line_id)
                full_childs = {}
                for child in direct_childs:
                    full_childs[child.id] = self.get_all_childs(child.id)

                line_id = None
                options["unfolded_lines"] = []
                holder_group = self.env["account.group"].browse(group_line_id)
                group_level = self.get_first_group(holder_group, "level")

        res = super(AccountGeneralLedgerReport, self)._get_lines(options, line_id=line_id)
        lang = self.env["res.lang"].search([["code", "=", self.env.user.lang]], limit=1)
        expr = r'[^0-9-' + lang.decimal_point + r']+'

        #Si es con jerarquia pero line_id esta establecido eso me quiere decir que la linea seleccionado es una cuenta
        #por lo que se retorna super, pero se tienen que corregir el valor de nivel
        if with_hierarchy and line_id:
            holder = False
            if "loadmore_" in line_id and res:
                to_convert = res[0]["parent_id"][8:]
                holder = int(to_convert)
            else:
                holder = int(line_id[8:])

            if holder:
                acc_holder = self.env["account.account"].browse(holder)
                glevel = self.get_first_group(acc_holder.group_id, "level")
                #Si solo le sumo glevel, queda un poco mas alla del nivel que tenia originalmente, por eso lo hago asi
                glevel -= 1
                if acc_holder.group_id:
                    res[0]["parent_id"] = "__group_{0}".format(acc_holder.group_id.id)

                for line in res:
                    if "level" in line:
                        line["level"] = line["level"] + glevel
                    else:
                        line["level"] = glevel + 2

        if with_hierarchy and not line_id:
            accounts = list(filter(lambda x: "account_" in str(x["id"]), res))
            first_groups = {}
            selected_group = []
            secondary_groups = {}
            target_groups = {}
            target_group = False
            next_level = 1 if not group_line_id else group_level + 1
            acc_ids = []

            for acc in accounts:
                target_group = False
                group = self.get_account_group(acc)

                #Si se desplego una linea que es un grupo he de recuperar las cuentas que van por debajo del mismo
                #asi como los grupos que sean sus hijos directos
                if group_line_id:
                    target_groups = secondary_groups
                    if group.id == group_line_id:
                        acc["level"] = next_level
                        parent_group = "__group_{0}".format(group.id)
                        acc["parent_id"] = parent_group
                        selected_group.append(acc)
                        acc_id = acc["id"][8:]
                        acc_id = int(acc_id)
                        acc_ids.append(acc_id)
                    else:
                        #o si el grupo de la cuenta es un hijo directo
                        if group.id in direct_childs.ids:
                            #Para este caso no es mostraria la cuenta sino el grupo
                            target_group = group
                        else:
                            #Si el grupo de la cuenta no es un hijo directo, pero es un hijo de algunos de los hijos de los hijos directos
                            #del grupo clickeado, la cuenta ha de sumar el total de ese hijo directo
                            for child in direct_childs:
                                if group.id in full_childs[child.id]:
                                    target_group = child
                                    break

                else:
                    #LLamo a una funcion que me retorna el mismo grupo si no tiene padre o su padre en el primer nivel
                    target_group = False
                    if group:
                        target_group = self.get_first_group(group)
                    target_groups = first_groups

                if target_group:
                    if target_group.id not in target_groups:
                        group_id = "__group_{0}".format(target_group.id)

                        target_cols = []
                        for x in range(0, len(acc["columns"])):
                            # Ahora en acc["columns"] vienen menos columnas y todas con un valor numerico, lo que es una
                            # diferencia en relacion a la version 13
                            val = self.format_value(0)

                            vals = {'name': val, 'class': 'number'}
                            target_cols.append(vals)

                        target_groups[target_group.id] = {'id': group_id, 'name': target_group.display_name.strip(), 'title_hover': target_group.display_name.strip(),
                                                          "columns": target_cols, "level": next_level, "unfoldable": True, "unfolded": False, 'colspan': 4}
                        if target_group.parent_id:
                            parent_group = "__group_{0}".format(target_group.parent_id.id)
                            target_groups[target_group.id]["parent_id"] = parent_group

                    #En la columna solo hay una cadena vacia, por eso el rango va del 1 en adelante
                    for x in range(0, len(acc["columns"])):
                        #Valor del grupo
                        holder = target_groups[target_group.id]["columns"][x]
                        curr_total = self.clean_value(holder["name"], expr)

                        #Valor de la cuenta actual
                        acc_holder = acc["columns"][x]
                        acc_value = self.clean_value(acc_holder["name"], expr)

                        curr_total += acc_value
                        new_val = self.format_value(curr_total)
                        holder["name"] = new_val

            result = []
            if group_line_id:
                col_qty = 1
                if selected_group:
                    col_qty = len(selected_group[0]["columns"])

                if target_groups:
                    holder = next(iter(target_groups.values()))
                    col_qty = len(holder["columns"])

                col_values = [0] * col_qty
                for item in selected_group:
                    for x in range(0, col_qty):
                        holder = item["columns"][x]
                        clean = self.clean_value(holder["name"], expr)
                        col_values[x] += clean

                #Que los grupos aparezcan antes que las cuentas
                for key in secondary_groups:
                    for x in range(0, col_qty):
                        holder = secondary_groups[key]["columns"][x]
                        clean = self.clean_value(holder["name"], expr)
                        col_values[x] += clean

                target_cols = []
                for x in range(0, col_qty):
                    holder = self.format_value(col_values[x])
                    vals = {"name": holder, "class": "number"}
                    target_cols.append(vals)

                holder_name = "__group_{0}".format(holder_group.id)
                og_line = {'id': holder_name, 'name': holder_group.display_name.strip(), 'title_hover': holder_group.display_name.strip(),
                           "columns": target_cols, "level": group_level, "unfoldable": True, "unfolded": True, 'colspan': 4}

                if holder_group.parent_id:
                    parent_group = "__group_{0}".format(holder_group.parent_id.id)
                    og_line["parent_id"] = parent_group

                result.append(og_line)

            #Se tiene que devolver una listado de diccionarios
            group_ids = list(target_groups.keys())
            #Itero los grupos que en el recordset estan ordenados
            groups = self.env["account.group"].search([["id", "in", group_ids]], order="code_prefix_start asc")
            for group in groups:
                holder = target_groups[group.id]
                result.append(holder)

            if selected_group:
                accounts = self.env["account.account"].search([["id", "in", acc_ids]], order="code asc")
                for account in accounts:
                    acc_id = "account_{0}".format(account.id)
                    acc_holder = list(filter(lambda x: acc_id == str(x["id"]), selected_group))
                    holder = acc_holder[0]
                    result.append(holder)

            return result

        return res
