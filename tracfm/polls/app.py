from django.conf import settings
from datetime import datetime

from rapidsms.models import Connection, Backend
from rapidsms.apps.base import AppBase
from rapidsms_httprouter.router import get_router

from .models import *

class App (AppBase):

    def handle (self, message):
        try:
            # check if our respondent is changing their active status
            respondent = Respondent.get_respondent(message)
            active_flag = respondent.get_active_flag(message)
            
            if active_flag:
                turn_on = active_flag == "on"
                turn_off = active_flag == "off"
                reset = active_flag == "reset"
                response = None

                if turn_on or turn_off:
                    if respondent.set_active_status(turn_on):
                        if turn_on:
                            response = TracSettings.get_setting(message.connection.backend, 'trac_on_response')
                        else:
                            response = TracSettings.get_setting(message.connection.backend, 'trac_off_response')
                            
                elif reset:
                    for poll in Poll.objects.filter(demographic=True, always_update=True):
                        poll.clear_response(message.db_message)

                    response = TracSettings.get_setting(message.connection.backend, 'trac_reset_response')

                # if our active flag was found, we don't look at any polls
                if response:
                    message.respond(response)

                return True

            # update the responses for polls that update on every message
            for poll in Poll.objects.filter(demographic=True, always_update=True, backend=message.connection.backend):
                poll.update_response(message.db_message)

            # find any matching poll
            poll = Poll.find_poll(message.text, message.connection.backend)

            # we found a matching poll?  process it
            if poll:
                response = poll.process_message(message.db_message)

                # no response to send
                if not response:
                    return True

                # active responses get category responses
                if response.active:
                    response_text = poll.message

                    # if we got classified, send back the response for that category
                    if response.category:
                        if response.category.message:
                            response_text =  response.category.message

                        # if the user is not active, pester them to become active
                        if not response.respondent.active:
                            recruitment_msg = TracSettings.get_setting(message.connection.backend, 'recruitment_message')
                            if recruitment_msg.strip():
                                response_text = "%s %s" % (response_text, recruitment_msg)
                    else:
                        response_text = poll.unknown_message

                    if response_text:
                        message.respond(response_text)
                        return True
                    else:
                        return False

                # inactive responses get the duplicate message
                else:
                    response = TracSettings.get_setting(message.connection.backend, 'duplicate_message')
                    if response:
                        message.respond(response)
                    return True

            return False

        except:
            import traceback
            traceback.print_exc()
            message.respond("An error occurred, please try again later.")
            return False
