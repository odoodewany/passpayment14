# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = "account.move"

	# name = fields.Char(compute="_compute_name_by_sequence")

	@api.model
	def _search_default_journal(self, journal_types):
		company_id = self._context.get('default_company_id', self.env.company.id)
		domain = [('company_id', '=', company_id), ('type', 'in', journal_types)]

		# journals_uid = self.env.user.sale_journal_ids
		# if 'sale' in journal_types and journals_uid:
		# 	domain = [('id', 'in', journals_uid.ids)]

		journal = None
		if self._context.get('default_currency_id'):
			currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
			journal = self.env['account.journal'].search(currency_domain, limit=1)

		if not journal:
			journal = self.env['account.journal'].search(domain, limit=1)

		if not journal:
			company = self.env['res.company'].browse(company_id)

			error_msg = _(
				"No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
				company_name=company.display_name,
				journal_types=', '.join(journal_types),
			)
			raise UserError(error_msg)

		return journal	

	@api.model
	def _get_default_journal(self):
		''' Get the default journal.
		It could either be passed through the context using the 'default_journal_id' key containing its id,
		either be determined by the default type.
		'''
		move_type = self._context.get('default_move_type', 'entry')
		if move_type in self.get_sale_types(include_receipts=True):
			journal_types = ['sale']
		elif move_type in self.get_purchase_types(include_receipts=True):
			journal_types = ['purchase']
		else:
			journal_types = self._context.get('default_move_journal_types', ['general'])

		if self._context.get('default_journal_id'):
			journal = self.env['account.journal'].browse(self._context['default_journal_id'])

			if move_type != 'entry' and journal.type not in journal_types:
				raise UserError(_(
					"Cannot create an invoice of type %(move_type)s with a journal having %(journal_type)s as type.",
					move_type=move_type,
					journal_type=journal.type,
				))
		else:
			journal = self._search_default_journal(journal_types)

		return journal

	@api.depends('company_id', 'invoice_filter_type_domain', 'move_type')
	def _compute_suitable_journal_ids(self):
		# journals_uid = self.env.user.sale_journal_ids
		for m in self:
			journal_type = m.invoice_filter_type_domain or 'general'
			company_id = m.company_id.id or self.env.company.id
			domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
			# if m.move_type == 'out_invoice' and journals_uid:
			# 	domain.append(('id', 'in', journals_uid.ids))
			m.suitable_journal_ids = self.env['account.journal'].search(domain)

	journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
		states={'draft': [('readonly', False)]}, 
		check_company=True, domain="[('id', 'in', suitable_journal_ids)]",
		default=_get_default_journal)

	@api.depends('posted_before', 'state', 'journal_id', 'date', 'l10n_latam_document_type_id', 'journal_id.is_sequence')
	def _compute_name(self):
		""" Change the way that the use_document moves name is computed:

		* If move use document but does not have document type selected then name = '/' to do not show the name.
		* If move use document and are numbered manually do not compute name at all (will be set manually)
		* If move use document and is in draft state and has not been posted before we restart name to '/' (this is
		   when we change the document type) """
		without_doc_type = self.filtered(lambda x: x.journal_id.l10n_latam_use_documents and not x.l10n_latam_document_type_id)
		manual_documents = self.filtered(lambda x: x.journal_id.l10n_latam_use_documents and x.l10n_latam_manual_document_number)
		(without_doc_type + manual_documents.filtered(lambda x: not x.name or x.name and x.state == 'draft' and not x.posted_before)).name = '/'
		# if we change document or journal and we are in draft and not posted, we clean number so that is recomputed in super
		self.filtered(
			lambda x: x.journal_id.l10n_latam_use_documents and x.l10n_latam_document_type_id
			and not x.l10n_latam_manual_document_number and x.state == 'draft' and not x.posted_before).name = '/'
		self = self - without_doc_type - manual_documents

		def journal_key(move):
			return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

		def date_key(move):
			return (move.date.year, move.date.month)

		grouped = defaultdict(  # key: journal_id, move_type
			lambda: defaultdict(  # key: first adjacent (date.year, date.month)
				lambda: {
					'records': self.env['account.move'],
					'format': False,
					'format_values': False,
					'reset': False
				}
			)
		)
		self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
		highest_name = self[0]._get_last_sequence() if self else False

		# Group the moves by journal and month
		for move in self:
			if not highest_name and move == self[0] and not move.posted_before and move.date:
				# In the form view, we need to compute a default sequence so that the user can edit
				# it. We only check the first move as an approximation (enough for new in form view)
				pass
			elif (move.name and move.name != '/') or move.state != 'posted':
				try:
					if not move.posted_before:
						move._constrains_date_sequence()
					# Has already a name or is not posted, we don't add to a batch
					continue
				except ValidationError:
					# Has never been posted and the name doesn't match the date: recompute it
					pass
			group = grouped[journal_key(move)][date_key(move)]
			if not group['records']:
				# Compute all the values needed to sequence this whole group
				move._set_next_sequence()
				group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
				if move.journal_id.is_sequence and not highest_name:
					group['format_values']['seq'] = move.journal_id.sequence_number_next or 1
				_logger.info(group['format_values'])
				group['reset'] = move._deduce_sequence_number_reset(move.name)
			group['records'] += move

		# Fusion the groups depending on the sequence reset and the format used because `seq` is
		# the same counter for multiple groups that might be spread in multiple months.
		final_batches = []
		for journal_group in grouped.values():
			journal_group_changed = True
			for date_group in journal_group.values():
				if (
					journal_group_changed
					or final_batches[-1]['format'] != date_group['format']
					or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
				):
					final_batches += [date_group]
					journal_group_changed = False
				elif date_group['reset'] == 'never':
					final_batches[-1]['records'] += date_group['records']
				elif (
					date_group['reset'] == 'year'
					and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
				):
					final_batches[-1]['records'] += date_group['records']
				else:
					final_batches += [date_group]

		# Give the name based on previously computed values
		for batch in final_batches:
			for move in batch['records']:
				move.name = batch['format'].format(**batch['format_values'])
				batch['format_values']['seq'] += 1
			batch['records']._compute_split_sequence()

		self.filtered(lambda m: not m.name).name = '/'
				

	@api.depends("state", "journal_id", "date")
	def _compute_name_by_sequence(self):
		for move in self:
			name = move.name or "/"
			if (
					move.state == "posted"
					and (not move.name or move.name == "/")
					and move.journal_id
					and move.journal_id.sequence_id
			):
				if (
						move.move_type in ("out_refund", "in_refund")
						and move.journal_id.type in ("sale", "purchase")
						and move.journal_id.refund_sequence
						and move.journal_id.refund_sequence_id
				):
					seq = move.journal_id.refund_sequence_id
				else:
					seq = move.journal_id.sequence_id
				name = seq.next_by_id(sequence_date=move.date)
			move.name = name

	def _constrains_date_sequence(self):
		return True

	# credit_note comment
	@api.constrains('move_type', 'l10n_latam_document_type_id')
	def _check_invoice_type_document_type(self):
		for rec in self.filtered('l10n_latam_document_type_id.internal_type'):
			internal_type = rec.l10n_latam_document_type_id.internal_type
			invoice_type = rec.move_type
			if internal_type in ['debit_note', 'invoice'] and invoice_type in ['out_refund', 'in_refund']:
				raise ValidationError(_('You can not use a %s document type with a refund invoice', internal_type))
			# elif internal_type == 'credit_note' and invoice_type in ['out_invoice', 'in_invoice']:
			# 	raise ValidationError(_('You can not use a %s document type with a invoice', internal_type))		


# class Users(models.Model):
# 	_inherit = "res.users"

# 	sale_journal_ids = fields.Many2many('account.journal', string='Diarios de Ventas', domain=[('type', '=', 'sale')], 
# 		help="Accounting journal used to post sales entries.")


# class SaleAdvancePaymentInv(models.TransientModel):
# 	_inherit = "sale.advance.payment.inv"

# 	def _default_sale_journal(self):
# 		request_search = [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)]
# 		journals_uid = self.env.user.sale_journal_ids
# 		if journals_uid:
# 			request_search = [('id', 'in', journals_uid.ids)]
# 		return self.env['account.journal'].search(request_search, limit=1)

# 	def _sale_journal_domain(self):
# 		request_search = [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)]
# 		journals_uid = self.env.user.sale_journal_ids
# 		if journals_uid:
# 			request_search = [('id', 'in', journals_uid.ids)]
# 		return request_search

# 	journal_id = fields.Many2one('account.journal', string='Diario de Ventas', domain=_sale_journal_domain, 
# 		help="Accounting journal used to post sales entries.", default=_default_sale_journal, ondelete='restrict')

# 	@api.onchange('journal_id')
# 	def _onchange_journal_id(self):
# 		""" When change journal_id, 
# 			Change journal_id in order.
# 		"""
# 		company_id = self._context.get('default_company_id', self.env.company.id)
# 		domain = [('company_id', '=', company_id), ('type', '=', 'sale')]
# 		if self._context.get('default_currency_id'):
# 			domain.append('currency_id', '=', self._context['default_currency_id'])
# 		journal = self.env['account.journal'].search(domain, order='sequence asc', limit=1)
# 		_logger.info(domain)
# 		_logger.info(journal)
# 		if journal and self.journal_id:
# 			sequence = journal.sequence
# 			journal.write({'sequence': self.journal_id.sequence})
# 			self.journal_id.write({'sequence': sequence})		

# 	def _prepare_invoice_values(self, order, name, amount, so_line):
# 		res = super()._prepare_invoice_values(order, name, amount, so_line)
# 		if self.journal_id:
# 			res.update({
# 				'journal_id': self.journal_id.id,
# 				# 'l10n_latam_document_type_id': self.journal_id.l10n_latam_document_type_id.id,
# 			})
# 		return res	
