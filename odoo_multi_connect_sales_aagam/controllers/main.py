# -*- coding: utf-8 -*-
import odoo
import base64
from odoo import http, SUPERUSER_ID
import werkzeug
from odoo.http import request
from odoo.tools import image_process
from odoo.addons.web.controllers.main import WebClient, Binary

import logging
_logger = logging.getLogger(__name__)


class Channel(http.Controller):

	# check unused
	@http.route(['/channel/update/mapping',],auth="public", type='json')
	def update_mapping(self, **post):
		model_info_dict = {
			'product.product': 'product.mapping',
			'sale.order': 'order.mapping',
		}
		field_info_dict = {
			'product.product': 'erp_product_id',
			'sale.order': 'odoo_order_id',
		}
		field = field_info_dict.get(str(post.get('model')))
		model = model_info_dict.get(str(post.get('model')))
		if field and model:
			domain = [(field, '=', int(post.get('id')))]
			mappings = request.env[model].sudo().search(domain)
			for mapping in mappings:pass
		return True


	def core_content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
					  filename_field='datas_fname', unique=None, filename=None, mimetype=None,
					  download=None, width=0, height=0, crop=False, access_token=None, **kwargs):
		contenttype = kwargs.get('ax_mime_type') or 'image/jpg'
		status, headers, content = request.env['ir.http'].sudo().binary_content(
			xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
			filename_field=filename_field, download=download, mimetype=mimetype,
			default_mimetype='image/jpg', access_token=access_token)
		if status == 304:
			return werkzeug.wrappers.Response(status=304, headers=headers)
		elif status == 301:
			return werkzeug.utils.redirect(content, code=301)
		elif status != 200 and download:
			return request.not_found()

		height = int(height or 0)
		width = int(width or 0)


		if crop and (width or height):
			content = image_process(content, size=(width, height),crop=crop,encoding='base64', output_format='PNG')


		elif content and (width or height):
			if width > 500:
				width = 500
			if height > 500:
				height = 500
			content = odoo.tools.image_process(content, size=(width or None, height or None), output_format='PNG')

		if content:
			image_base64 = base64.b64decode(content)
		else:
			image_base64 = Binary().placeholder()
			headers = Binary().force_contenttype(headers)
		headers.append(('Content-Length', len(image_base64)))
		response = request.make_response(image_base64, headers)
		response.status_code = status
		return response

	@http.route([
	'/channel/image.png',
	'/channel/image/<xmlid>.png',
	'/channel/image/<xmlid>/<int:width>x<int:height>.png',
	'/channel/image/<xmlid>/<field>.png',
	'/channel/image/<xmlid>/<field>/<int:width>x<int:height>.png',
	'/channel/image/<model>/<id>/<field>.png',
	'/channel/image/<model>/<id>/<field>/<int:width>x<int:height>.png',
	'/channel/image.jpg',
	'/channel/image/<xmlid>.jpg',
	'/channel/image/<xmlid>/<int:width>x<int:height>.jpg',
	'/channel/image/<xmlid>/<field>.jpg',
	'/channel/image/<xmlid>/<field>/<int:width>x<int:height>.jpg',
	'/channel/image/<model>/<id>/<field>.jpg',
	'/channel/image/<model>/<id>/<field>/<int:width>x<int:height>.jpg'
	], type='http', auth="public", website=False, multilang=False)
	def content_image(self, id=None, max_width=492, max_height=492, **kw):
		if max_width:
			kw['width'] = max_width
		if max_height:
			kw['height'] = max_height
		if id:
			id, _, unique = id.partition('_')
			kw['id'] = int(id)
			if unique:
				kw['unique'] = unique
		kw['ax_mime_type'] = 'image/jpg'
		return self.core_content_image(**kw)
