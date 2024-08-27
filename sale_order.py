import time
from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, default='New')

    is_booking_order = fields.Boolean(string='Is Booking Order')
    team_id = fields.Many2one(comodel_name='service.team', string='Team', ondelete='restrict')  # Added ondelete to handle relational integrity
    team_leader_id = fields.Many2one(comodel_name='res.users', string='Team Leader')
    team_members_ids = fields.Many2many(comodel_name='res.users', string='Team Members')
    booking_start = fields.Datetime(string='Booking Start', default=lambda self: time.strftime("%Y-%m-%d"))
    booking_end = fields.Datetime(string='Booking End', default=lambda self: time.strftime("%Y-%m-%d"))

    # team_name = fields.Char(string='Team Name', compute='_compute_team_name')

    # @api.depends('team_id')
    # def _compute_team_name(self):
    #     for record in self:
    #         record.team_name = record.team_id.team_id

    team_name = fields.Char(string='Team Name', related='team_id.name')

    # def unlink(self):
    #     for record in self:
    #         if record.team_id:  # Check if the record is linked to a team
    #             raise UserError("Cannot delete Sales Order because it is referenced by a Team.")
    #     return super(SaleOrder, self).unlink()

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            # Auto-fill the team leader and team members based on the selected team
            self.team_leader_id = self.team_id.team_leader.id
            self.team_members_ids = [(6, 0, self.team_id.team_members.ids)]
        else:
            # Clear the fields if no team is selected
            self.team_leader_id = False
            self.team_members_ids = [(5, 0, 0)]

    @api.onchange('team_id', 'booking_start', 'booking_end')
    def cek_overlap_time(self):
        if self.team_id and self.booking_start and self.booking_end:
            active_work_orders = self.env['work.order'].search([
                ('team_id', '=', self.team_id.id),
                ('state', '!=', 'cancelled'),
                ('planned_start', '<=', self.booking_end),
                ('planned_end', '>=', self.booking_start)
            ])
            if active_work_orders:
                return {
                    'warning': {
                        'title': "Team Unavailable",
                        'message': "Team already has a work order during that period on SO {self.name}"
                    }
                }
            else:
                return {
                    'info': {
                        'title': "Team Available",
                        'message': "Team is available for booking"
                    }
                }