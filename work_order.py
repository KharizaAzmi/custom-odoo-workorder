import time
from odoo import models, fields, api

class WorkOrder(models.Model):
    _name = 'work.order'
    _description = 'Work Order'

    name = fields.Char(string='WO Number', required=True, copy=False, readonly=True, default=lambda self: 'New')
    booking_order_id = fields.Many2one(comodel_name='sale.order', string='Booking Order Reference', readonly=True)
    team_id = fields.Many2one(comodel_name='service.team', string='Team', required=True)
    team_leader_id = fields.Many2one(comodel_name='res.users', string='Team Leader', required=True)
    team_members_ids = fields.Many2many(comodel_name='res.users', related='team_id.team_members', string='Team Members')
    planned_start = fields.Datetime(string='Planned Start', required=True, default=lambda self: time.strftime("%Y-%m-%d"))
    planned_end = fields.Datetime(string='Planned End', required=True, default=lambda self: time.strftime("%Y-%m-%d"))
    date_start = fields.Datetime(string='Date Start', readonly=True, default=lambda self: time.strftime("%Y-%m-%d"))
    date_end = fields.Datetime(string='Date End', readonly=True, default=lambda self: time.strftime("%Y-%m-%d"))
    state = fields.Selection([
        ('pending', 'Pending'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='State', default='pending')
    notes = fields.Text(string='Notes')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', related='booking_order_id.partner_id', store=True)

    team = fields.Char(string='Team Name', compute='_compute_team_name')

    @api.depends('team_id')
    def _compute_team_name(self):
        for record in self:
            record.team_name = record.team_id.name

    booking_order_name = fields.Char(string='Booking Order Name', compute='_compute_booking_order_name')

    @api.depends('booking_order_id')
    def _compute_booking_order_name(self):
        for record in self:
            record.booking_order_name = record.booking_order_id.name


    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            self.team_leader_id = self.team_id.team_leader.id
            self.team_members_ids = [(6, 0, self.team_id.team_members.ids)]
        else:
            self.team_leader_id = False
            self.team_members_ids = [(5, 0, 0)]

    @api.model
    def create(self, vals):
        # Generate WO Number
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('work.order') or 'New'
        
        # Filter non integer values from team_members_ids
        team_members_ids = [member_id for member_id in vals.get('team_members_ids', [])[0][2] if isinstance(member_id, int)]

        # Set booking_order_id
        sale_order = self.env['sale.order'].search([
            ('team_id', '=', vals.get('team_id')),
            ('team_leader_id', '=', vals.get('team_leader_id')),
            ('team_members_ids', 'in', team_members_ids)
        ], limit=1)
        
        if sale_order:
            vals['booking_order_id'] = sale_order.id

        result = super(WorkOrder, self).create(vals)
        return result

    def action_set_pending(self):
        self.write({'state': 'pending'})
    
    def action_set_progress(self):
        self.write({'state': 'progress'})

    def action_set_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
