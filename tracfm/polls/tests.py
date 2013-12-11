from django.test import TestCase

from django.contrib.auth.models import User, Group
from .models import *
from rapidsms_httprouter.models import Message
from rapidsms.models import *
from simple_locations.models import AreaType
from locations.models import Area
from django.core.exceptions import ObjectDoesNotExist
from .app import App

from .views import PollCategoryDeleteView

class PollTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("admin", "admin@domain.com", 'password')
        self.user.groups.add(Group.objects.get(name="Administrators"))

        self.host = User.objects.create_user('host', 'host@domain.com', 'password')
        self.host.groups.add(Group.objects.get(name="Radio Hosts"))

        self.host2 = User.objects.create_user('host2', 'host2@domain.com', 'password')
        self.host2.groups.add(Group.objects.get(name="Radio Hosts"))

        self.other_host = User.objects.create_user('other_host', 'host@domain.com', 'password')
        self.other_host.groups.add(Group.objects.get(name="Radio Hosts"))

        self.editor = User.objects.create_user('editor', 'editor@domain.com', 'password')
        self.editor.groups.add(Group.objects.get(name="Editors"))

        self.other_editor = User.objects.create_user('other_editor', 'editor@domain.com', 'password')
        self.other_editor.groups.add(Group.objects.get(name="Editors"))

        (self.backend, created) = Backend.objects.get_or_create(name='test')
        (self.other_backend, created) = Backend.objects.get_or_create(name='other')

        from trac_users.models import UserBackend
        UserBackend.objects.create(user=self.user, backend=self.backend)
        UserBackend.objects.create(user=self.host, backend=self.backend)
        UserBackend.objects.create(user=self.host2, backend=self.backend)
        UserBackend.objects.create(user=self.editor, backend=self.backend)

        UserBackend.objects.create(user=self.user, backend=self.other_backend)
        UserBackend.objects.create(user=self.other_host, backend=self.other_backend)
        UserBackend.objects.create(user=self.other_editor, backend=self.other_backend)

    def assertDemoPermissions(self, allowed):
        response = self.client.get(reverse('poll_demo_list'))
        self.assertEquals(200 if allowed else 302, response.status_code)

        response = self.client.get(reverse('poll_demo_create'))
        self.assertEquals(200 if allowed else 302, response.status_code)

    def assertCreationPermissions(self, allowed):
        response = self.client.get(reverse('poll_create'))
        self.assertEquals(200 if allowed else 302, response.status_code)

    def assertAdminPermissions(self, allowed):
        # can we see it in a list?
        response = self.client.get(reverse('polls.tracsettings_list'))
        self.assertEquals(200 if allowed else 302, response.status_code)

        # can we create a new one
        response = self.client.get(reverse('polls.tracsettings_create'))
        self.assertEquals(200 if allowed else 302, response.status_code)

        response = self.client.get(reverse('respondents'))
        self.assertEquals(200 if allowed else 302, response.status_code)

        response = self.client.get(reverse('respondent_view', args=[1]))
        self.assertEquals(200 if allowed else 302, response.status_code)

        #response = self.client.get(reverse('respondent_edit', args=[1]))
        #self.assertEquals(200 if allowed else 302, response.status_code)

    def assertReadPermissions(self, poll, allowed):
        # can we see it in a list?
        list_page = self.client.get(reverse('polls'))
        self.assertEquals(allowed, poll in list_page.context['poll_list'])

        # can we view it?
        response = self.client.get(reverse('poll_view', args=[poll.id]))
        self.assertEquals(200 if allowed else 302, response.status_code)

        # can we see the iframe?
        response = self.client.get(reverse('poll_iframe', args=[poll.id]))
        self.assertEquals(200 if allowed else 302, response.status_code)

        # can we see the responses
        response = self.client.get(reverse('responses_for_poll', args=[poll.id]))
        self.assertEquals(200 if allowed else 302, response.status_code)

        # and responses for a particular category
        response = self.client.get(reverse('responses_for_poll', args=[poll.id, '_']))
        self.assertEquals(200 if allowed else 302, response.status_code)

    def assertCanCreateCategorySet(self, canCreate):
        # can we create a new one
        response = self.client.get(reverse('catset_add'))
        self.assertEquals(200 if canCreate else 302, response.status_code)

    def assertCategorySetPermissions(self, canRead, canWrite):
        # can we see a list of category sets?
        response = self.client.get(reverse('catsets_list'))
        self.assertEquals(200 if canRead else 302, response.status_code)

        # can we see the detail view for a category set
        response = self.client.get(reverse('catset_view', args=[1]))
        self.assertEquals(200 if canRead else 302, response.status_code)

        # can we edit it
        response = self.client.get(reverse('catset_edit', args=[1]))
        self.assertEquals(200 if canWrite else 302, response.status_code)

        # can we delete it
        response = self.client.get(reverse('catset_delete', args=[1]))
        self.assertEquals(200 if canWrite else 302, response.status_code)

        # can we create a new category
        response = self.client.get(reverse('category_create', args=[1]))
        self.assertEquals(200 if canWrite else 302, response.status_code)

        # can we update an existing one
        response = self.client.get(reverse('category_edit', args=[1, 1]))
        self.assertEquals(200 if canWrite else 302, response.status_code)

    def assertWritePermissions(self, poll, allowed):
        # can we update it
        response = self.client.get(reverse('poll_edit', args=[poll.id]))
        self.assertEquals(200 if allowed else 302, response.status_code)

        # can we delete it
        response = self.client.get(reverse('poll_delete', args=[poll.id]))
        self.assertEquals(200 if allowed else 302, response.status_code)

        # can we edit responses?
        response = self.client.get(reverse('response_categorization', args=[poll.id, '_']))
        self.assertEquals(200 if allowed else 302, response.status_code)

        # can we start it
        response = self.client.get(reverse('poll_start', args=[poll.id]))
        poll = Poll.objects.get(pk=poll.id)
        if allowed:
            self.assertTrue(poll.started)
        else:
            self.assertFalse(poll.started)
            poll.start()

        # can we stop it
        response = self.client.get(reverse('poll_stop', args=[poll.id]))
        poll = Poll.objects.get(pk=poll.id)
        if allowed:
            self.assertTrue(poll.ended)
        else:
            self.assertFalse(poll.ended)

        poll.started = None
        poll.ended = None
        poll.save()

    def test_settings(self):
        app = App(None)

        # create default settings
        TracSettings.objects.create(backend=None,
                                    trac_on_response="trac on response",
                                    trac_off_response="trac off response",
                                    trac_reset_response="trac reset response",
                                    recruitment_message="recruitment message",
                                    duplicate_message="duplicate message")

        self.assertFalse(app.handle(get_rapid_message(1, "test message")))

        # create a poll with no keyword
        poll = Poll.objects.create(name="no keyword",
                                   description="desc",
                                   message="this is the default response",
                                   unknown_message="unrecognized response",
                                   backend=self.backend,
                                   user=self.user)
        
        # add a single category
        cat = poll.categories.create(name="category")
        rule = cat.rules.create(match="red")

        # start this poll
        poll.start()

        # should be handled by the poll then
        msg = get_rapid_message(1, "test message 2", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertEquals("unrecognized response", msg.responses[0].text)

        # send a valid category this time
        msg = get_rapid_message(1, "red", self.backend)
        self.assertTrue(app.handle(msg))

        # should get the default response and a recruitment message
        self.assertEquals("this is the default response recruitment message", msg.responses[0].text)

        # doing it again, should get us the duplicate message
        msg = get_rapid_message(1, "red", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertEquals("duplicate message", msg.responses[0].text)

        # do some trac on action
        msg = get_rapid_message(1, "trac on", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertEquals("trac on response", msg.responses[0].text)

        # and trac off
        msg = get_rapid_message(1, "trac off", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertEquals("trac off response", msg.responses[0].text)

        # finally reset
        msg = get_rapid_message(1, "trac reset", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertEquals("trac reset response", msg.responses[0].text)

        # create a settings object that is customized to our particular backend
        TracSettings.objects.create(backend=self.backend,
                                    duplicate_message="custom duplicate")

        # this message will actually get ignored, as the user has sent too many for this poll
        msg = get_rapid_message(1, "red", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertFalse(msg.responses)

        # different connection will work though
        msg = get_rapid_message(3, "red", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertEquals('this is the default response', msg.responses[0].text)

        # duplicate
        msg = get_rapid_message(3, "red", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertEquals('custom duplicate', msg.responses[0].text)

        # trac on
        msg = get_rapid_message(3, "trac on", self.backend)
        self.assertTrue(app.handle(msg))
        self.assertFalse(msg.responses)

    def test_host_web_view(self):
        # log in as a host
        self.client.login(username='host', password='password')

        # go to create a poll
        post_data = dict(name="Are you happy?",
                         keywords="test",
                         backend=self.backend.id,
                         description="This is my test poll",
                         message="Thanks for sending in your opinion",
                         unknown_message="Unknown response, sorry",
                         template="-1",
                         categories="Yes: yes, y\nNo: no, n",
                         secondary_template='0',
                         is_public=False)

        response = self.client.post(reverse('poll_create'), post_data)

        self.assertEqual(302, response.status_code)
        poll = Poll.objects.get(name='Are you happy?')

        # assert our categories
        self.assertEquals(2, poll.categories.count())
        self.assertEquals("Yes", poll.categories.all()[0].name)
        self.assertEquals("No", poll.categories.all()[1].name)

        # not public
        self.assertFalse(poll.is_public)

        # not started
        self.assertFalse(poll.started)

        # create a response
        message = get_message('250788123123', 'yes yes', self.backend)
        respondent = Respondent.get_respondent(message)
        response = poll.process_message(message)

        # check our permissions permissions
        self.assertReadPermissions(poll, True)
        self.assertWritePermissions(poll, True)
        self.assertDemoPermissions(False)
        self.assertCategorySetPermissions(True, True)
        self.assertCanCreateCategorySet(True)
        self.assertAdminPermissions(False)

        # log out
        self.client.logout()

        # check our anonymous permissions
        self.assertReadPermissions(poll, False)
        self.assertWritePermissions(poll, False)
        self.assertDemoPermissions(False)
        self.assertCategorySetPermissions(False, False)
        self.assertCanCreateCategorySet(False)
        self.assertAdminPermissions(False)

        # log in as another host on the same backend
        self.client.login(username='host2', password='password')

        # should be able to see, but not edit
        self.assertReadPermissions(poll, True)
        self.assertWritePermissions(poll, False)
        self.assertDemoPermissions(False)
        self.assertCategorySetPermissions(True, False)
        self.assertCanCreateCategorySet(True)
        self.assertAdminPermissions(False)

        # log in as an editor on that backend
        self.client.login(username='editor', password='password')

        # check that this editor can read and write
        self.assertReadPermissions(poll, True)
        self.assertWritePermissions(poll, True)
        self.assertDemoPermissions(True)
        self.assertCategorySetPermissions(True, True)
        self.assertCanCreateCategorySet(True)
        self.assertAdminPermissions(False)

        # log in as an admin
        self.client.login(username='admin', password='password')

        # check that this editor can read and write
        self.assertReadPermissions(poll, True)
        self.assertWritePermissions(poll, True)
        self.assertDemoPermissions(True)
        self.assertCategorySetPermissions(True, True)
        self.assertCanCreateCategorySet(True)
        self.assertAdminPermissions(True)

        # log in as an editor on the other backend
        self.client.login(username='other_editor', password='password')

        # check that this editor has no access since he is on another backend
        self.assertReadPermissions(poll, False)
        self.assertWritePermissions(poll, False)
        self.assertDemoPermissions(True)
        self.assertCategorySetPermissions(True, True)
        self.assertCanCreateCategorySet(True)
        self.assertAdminPermissions(False)

        # log back in as the original host
        self.client.login(username='host', password='password')

        # create a poll on another backend
        other_poll = Poll.objects.create(name="Poll on other backend",
                                   description="desc",
                                   message="this is the default response",
                                   unknown_message="unrecognized response",
                                   backend=self.other_backend,
                                   is_public=True,
                                   user=self.other_host)

        # this user shouldn't see the other poll, even if it is public as it is on another backend
        list_page = self.client.get(reverse('polls'))
        self.assertFalse(other_poll in list_page.context['poll_list'])

        # make it public now
        post_data['is_public'] = True
        del post_data['template']
        del post_data['categories']
        response = self.client.post(reverse('poll_edit', args=[poll.id]), post_data)
        
        poll = Poll.objects.get(pk=poll.pk)
        self.assertTrue(poll.is_public)

        # our own permissions haven't changed
        self.assertReadPermissions(poll, True)
        self.assertWritePermissions(poll, True)

        # make sure we can see it logged out now
        self.client.logout()

        self.assertReadPermissions(poll, True)
        self.assertWritePermissions(poll, False)

        # log in as another host on another backend, shouldn't see it
        self.client.login(username='other_host', password='password')
        self.assertReadPermissions(poll, False)
        self.assertWritePermissions(poll, False)        

        # same with an editor
        self.client.login(username='other_editor', password='password')
        self.assertReadPermissions(poll, False)
        self.assertWritePermissions(poll, False)        

        # but our own editor can
        self.client.login(username='editor', password='password')
        self.assertReadPermissions(poll, True)
        self.assertWritePermissions(poll, True)

        # and host2 can read but still not edit
        self.client.login(username='host2', password='password')
        self.assertReadPermissions(poll, True)
        self.assertWritePermissions(poll, False)

        # shouldn't be able to find the poll because it isn't active
        self.assertEquals(None, Poll.find_poll("test", self.backend))        

        # log back in
        self.client.login(username='host', password='password')

        # make the poll active
        response = self.client.get(reverse('poll_start', args=[poll.id]))
        
        poll = Poll.objects.get(pk=poll.pk)
        self.assertTrue(poll.started)
        self.assertEquals(poll, Poll.find_poll("test", self.backend))        

        # stop the poll
        response = self.client.get(reverse('poll_stop', args=[poll.id]))

        poll = Poll.objects.get(pk=poll.pk)
        self.assertTrue(poll.ended)
        self.assertEquals(None, Poll.find_poll("test", self.backend))

    def test_find_poll(self):
        # Tests finding a poll using a keyword.

        # no polls, no match
        self.assertEquals(None, Poll.find_poll("hello", self.backend))

        user = User.objects.create(username="test")
        no_keyword = Poll.objects.create(name="no keyword",
                                         description="desc",
                                         message="msg",
                                         backend=self.backend,
                                         user=user)

        clue = Poll.objects.create(name="clue keyword",
                                   description="desc",
                                   message="msg",
                                   backend=self.backend,
                                   user=user)

        clue.keywords.create(name="clue")

        glue = Poll.objects.create(name="glue keyword",
                                   description="desc",
                                   message="msg",
                                   backend=self.backend,
                                   user=user)

        glue.keywords.create(name="GLUE")

        self.assertEquals(None, Poll.find_poll("", self.backend))

        # no polls are active, shouldn't find any
        self.assertEquals(None, Poll.find_poll("test foo", self.backend))

        # activate the glue poll
        glue.start()

        # still shouldn't match
        self.assertEquals(None, Poll.find_poll("test foo", self.backend))

        # activate the no keyword poll
        no_keyword.start()

        # now we match on our normal backend
        self.assertEquals(no_keyword, Poll.find_poll("test foo", self.backend))

        # but not our other backend
        self.assertEquals(None, Poll.find_poll("test foo", self.other_backend))

        # but a specific keyword should match
        self.assertEquals(glue, Poll.find_poll("glue foo", self.backend))

        # only on right backend
        self.assertEquals(None, Poll.find_poll("glue foo", self.other_backend))

        # including fuzzy
        self.assertEquals(glue, Poll.find_poll("clue foo", self.backend))

        # but if we activate our exact poll
        clue.start()

        # then it should match
        self.assertEquals(clue, Poll.find_poll("clue foo", self.backend))

        # until it is turned off
        clue.end()

        # then it should match
        self.assertEquals(glue, Poll.find_poll("clue foo", self.backend))

        # turn that one off too
        glue.end()

        # we now match our default poll
        self.assertEquals(no_keyword, Poll.find_poll("clue foo", self.backend))

        # until we shut it down too
        no_keyword.end()
        self.assertEquals(None, Poll.find_poll("clue foo", self.backend))        

    def test_rule_matching(self):
        # Tests our matching logic for rules.
        user = User.objects.create(username="test")
        poll = Poll.objects.create(name="favorite color",
                                   description="desc",
                                   message="msg",
                                   backend=self.backend,
                                   user=user)

        # our test category
        cat = poll.categories.create(name="category")

        # create a rule
        rule = cat.rules.create(match="red")

        # strict matching
        self.assertTrue(rule.matches("RED"))
        self.assertTrue(rule.matches("the cat is RED"))
        self.assertTrue(rule.matches("myfavorite color is red"))
        self.assertTrue(rule.matches(" red "))
        self.assertTrue(rule.matches(" red!"))
        self.assertTrue(rule.matches(".red!"))

        # things that shouldn't match
        self.assertFalse(rule.matches("rad"))
        self.assertFalse(rule.matches("rod"))
        self.assertFalse(rule.matches("re do"))        
        self.assertFalse(rule.matches("redd"))
        self.assertFalse(rule.matches("drednaught"))                

        # edit distance matching
        self.assertTrue(rule.matches("RaD", True))
        self.assertTrue(rule.matches("ReDd", True))

        # too far
        self.assertFalse(rule.matches("drednaught", True))
        self.assertFalse(rule.matches("dreads", True))

        # multi word rule
        rule.match = "red panda"
        rule.save()

        # strict matching
        self.assertTrue(rule.matches("RED IS FOR PANDA"))
        self.assertTrue(rule.matches("my panda is red and cute"))
        self.assertTrue(rule.matches("I once painted my panda red"))
        self.assertTrue(rule.matches("red panda!!"))
        self.assertTrue(rule.matches("PANDA RED"))

        # things that shouldn't match
        self.assertFalse(rule.matches("red pandas"))
        self.assertFalse(rule.matches("reds panda"))
        self.assertFalse(rule.matches("pandamoniom is red"))

        # edit distance matching
        self.assertTrue(rule.matches("I love red pandas", True))
        self.assertTrue(rule.matches("Your face is like a rad panda", True))
        self.assertTrue(rule.matches("Your face is like a rad penda", True))        

        # too far
        self.assertFalse(rule.matches("Your face is not a very penda rads", True))

    def test_category_matching(self):
        # Tests that categories are appropriately matched according to the rules they have set.
        user = User.objects.create(username="test")

        poll = Poll.objects.create(name="favorite color",
                                   description="desc",
                                   message="msg",
                                   backend=self.backend,
                                   user=user)

        # add some categories
        blue = poll.categories.create(name="blue")
        blue.rules.create(match="blue")
        blue.rules.create(match="azure")
        
        green = poll.categories.create(name="green")
        green.rules.create(match="green")
        green.rules.create(match="blue")  # this is a duplicate on purpose
        
        red = poll.categories.create(name="red")
        red.rules.create(match="red")
        red.rules.create(match="grean") # fuzzy match

        self.assertEquals(red, poll.find_category("red panda", poll.categories))
        self.assertEquals(red, poll.find_category("rad panda", poll.categories))

        # dupe rule, should match blue first though
        self.assertEquals(blue, poll.find_category("blue panda", poll.categories))

        # alternate rule
        self.assertEquals(blue, poll.find_category("azure", poll.categories))

        # first letter has to be the same
        self.assertEquals(None, poll.find_category("zaure", poll.categories))

        # transposition
        self.assertEquals(blue, poll.find_category("aUzrE", poll.categories))

        # matches real first
        self.assertEquals(green, poll.find_category("green", poll.categories))
        
        # fuzzy alternate rule
        self.assertEquals(blue, poll.find_category("azule", poll.categories))

        # more fuzzy
        self.assertEquals(blue, poll.find_category("blues", poll.categories))

        # no matches
        self.assertEquals(None, poll.find_category("yellow", poll.categories))
        self.assertEquals(None, poll.find_category("your panda is a dumb color", poll.categories))
        self.assertEquals(None, poll.find_category("i eat pandas with ice cream", poll.categories))
        
    def test_one_active(self):
        # Tests that we enforce only having one poll active at a time with a particular keyword.
        user = User.objects.create(username="test")
        poll = Poll.objects.create(name="test poll",
                                   description="desc",
                                   message="msg",
                                   backend=self.backend,
                                   user=user)

        # try to start the poll, should work fine
        poll.start()

        self.assertTrue(poll.active())

        # and should end fine as well
        poll.end()

        # try with another poll
        poll1 = Poll.objects.create(name="test poll 1",
                                    description="desc",
                                    message="msg",
                                    backend=self.backend,
                                    user=user)

        poll2 = Poll.objects.create(name="test poll 2",
                                    description="desc",
                                    message="msg",
                                    backend=self.backend,
                                    user=user)

        # start the first poll
        poll1.start()
        self.assertTrue(poll1.active())

        # try to start the second, should fail since the first has already been started
        self.assertRaises(Exception, poll2.start)


        # but a third poll on a different backend should be possible
        poll4 = Poll.objects.create(name="test poll 4",
                                    description="desc",
                                    message="msg",
                                    backend=self.other_backend,
                                    user=user)

        poll4.start()
        self.assertTrue(poll4.active())

        # try adding a new poll that has a keyword and start it
        poll3 = Poll.objects.create(name="test poll 3",
                                    description="desc",
                                    message="msg",
                                    backend=self.backend,
                                    user=user)
        poll3.keywords.create(name="keyword")
        
        poll3.start()
        self.assertTrue(poll3.active())

        # end the first poll
        poll1.end()

        # now we can start the second
        poll2.start()
        self.assertTrue(poll2.active())
        

    def test_dupe_response(self):
        """
        Tests that we only record the first response from a particular number
        """
        user = User.objects.create(username="test")
        poll = Poll.objects.create(name="favorite color",
                                   description="desc",
                                   message="msg",
                                   backend=self.backend,
                                   user=user)

        conn1 = Connection.objects.create(backend=self.backend, identity='123')

        msg1 = Message.objects.create(connection=conn1,
                                      text="hello world")

        # process this message
        response = poll.process_message(msg1)

        # should be one active response
        self.assertEquals(1, len(poll.responses.all()))

        msg2 = Message.objects.create(connection=conn1,
                                      text="foo bar")
        response = poll.process_message(msg2)        

        # should be one active response
        self.assertEquals(1, len(poll.responses.all()))
    
    def test_multiple_keywords(self):
        user = User.objects.create(username="test")

        poll = Poll.objects.create(name="favorite color",
                                   description="desc",
                                   message="msg",
                                   backend=self.backend,
                                   user=user)
        poll.set_keywords("eugene nic")
        poll.save()

        red = poll.categories.create(name="red")
        red.set_rules("red")
        red.save()

        (backend, created) = Backend.objects.get_or_create(name="test")
        conn1 = Connection.objects.create(backend=self.backend, identity='1')
        conn2 = Connection.objects.create(backend=self.backend, identity='2')
        conn3 = Connection.objects.create(backend=self.backend, identity='3')

        poll.start()

        # send some messages
        self.handle_message(Message.objects.create(connection=conn1, text="nic red"))
        self.assertEquals(1, PollResponse.objects.filter(category=red).count())

        self.handle_message(Message.objects.create(connection=conn2, text="eugene red"))
        self.assertEquals(2, PollResponse.objects.filter(category=red).count())

        # test non-matching keyword
        self.handle_message(Message.objects.create(connection=conn3, text="eric red"))
        self.assertEquals(2, PollResponse.objects.filter(category=red).count())

    def handle_message(self, message):
        poll = Poll.find_poll(message.text, message.connection.backend)
        if poll:
            return poll.process_message(message)


    def test_category_delete(self):
        user = User.objects.create(username="test")

        poll = Poll.objects.create(name="favorite color",
                                   description="desc",
                                   message="msg",
                                   backend=self.backend,
                                   user=user)

        red = poll.categories.create(name="red")
        red.set_rules("red")
        red.save()

        green = poll.categories.create(name="green")
        green.set_rules("green")
        green.save()

        blue = poll.categories.create(name="blue")
        blue.set_rules("blue")
        blue.save()
        
        poll.start()

        # send some messages
        (backend, created) = Backend.objects.get_or_create(name="test")
        conn1 = Connection.objects.create(backend=self.backend, identity='1')
        conn2 = Connection.objects.create(backend=self.backend, identity='2')
        conn3 = Connection.objects.create(backend=self.backend, identity='3')
        conn4 = Connection.objects.create(backend=self.backend, identity='4')

        # send some messages
        poll.process_message(Message.objects.create(connection=conn1, text="red"))
        poll.process_message(Message.objects.create(connection=conn2, text="green"))
        poll.process_message(Message.objects.create(connection=conn3, text="blue"))
        poll.process_message(Message.objects.create(connection=conn4, text="chicken"))

        self.assertEquals(4, poll.count())
        self.assertEquals(1, poll.unknown_count())

        # delete and check poll counts
        red.delete()
        self.assertEquals(3, poll.count())
        self.assertEquals(1, poll.unknown_count())


    def test_category_template(self):
        user = User.objects.create(username="test")

        # create a template category set
        template = PollCategorySet.objects.create(name="template", user=user)

        red = template.categories.create(name="red", message="red category")
        red.set_rules("red")
        red.save()

        green = template.categories.create(name="green", message="green category")
        green.set_rules("green")
        green.save()

        blue = template.categories.create(name="blue", message="blue category")
        blue.set_rules("blue")
        blue.save()

        # create a poll off of our template
        poll = Poll.objects.create(name="favorite color",
                                   description="desc",
                                   message="msg",
                                   user=user,
                                   backend=self.backend,
                                   template=template)


        # test that our poll categories are a copy of the template
        self.assertEquals(template.categories.count(), poll.categories.count())
        template_categories = template.categories.all()
        idx = 0

        for category in poll.categories.all():

            # should have the same name
            self.assertEquals(template_categories[idx].name, category.name)

            # the same message
            self.assertEquals(template_categories[idx].message, category.message)

            # the same location
            self.assertEquals(template_categories[idx].latitude, category.latitude)
            self.assertEquals(template_categories[idx].longitude, category.longitude)

            # and the same rules
            self.assertEquals(template_categories[idx].get_rules(), category.get_rules())

            # but the ids should be different
            self.assertNotEquals(template_categories[idx].pk, category.pk)
            idx = idx + 1

        # modifying our categories should not affect the template
        red_cat = poll.categories.all()[0]
        red_cat.name = "maroon is a shade of red"
        red_cat.set_rules("green\nis\nthe\nnew\nred")
        red_cat.save()

        self.assertNotEqual(poll.categories.all()[0].name, template.categories.all()[0].name)
        self.assertNotEqual(poll.categories.all()[0].get_rules(), template.categories.all()[0].get_rules())

    def test_secondary_category_poll(self):
        user = User.objects.create(username="test")

        # create a template category set
        yes_no = PollCategorySet.objects.create(name="yes_no", user=user)

        yes = yes_no.categories.create(name="yes", message="Yes Category")
        yes.set_rules("yes")
        yes.save()

        no = yes_no.categories.create(name="no", message="No Category")
        no.set_rules("no")
        no.save()

        # create a poll with our secondary categories
        poll = Poll.objects.create(name="Location Yes No",
                                   description="desc",
                                   message="msg",
                                   user=user,
                                   backend=self.backend,
                                   secondary_template=yes_no)

        # create a couple primary categories
        kololo = poll.categories.create(name="Kololo", message="kololo")
        kololo.set_rules("kololo")
        kololo.save()

        karumbi = poll.categories.create(name="Karumbi", message="karumbi")
        karumbi.set_rules("karumbi")
        karumbi.save()

        # these were cloned from a template, so we need to fetch them to compare
        yes = poll.secondary_categories.get(name='yes')
        no = poll.secondary_categories.get(name='no')

        self.validate_categories(poll, kololo, yes, ['kololo yes', 'yes kololo', ' yse kololo ', 'live koollo yse.#'])
        self.validate_categories(poll, karumbi, yes, ['karumbi yes', 'yes karumib ', ' yse karimbi ', 'karumib yes'])
        self.validate_categories(poll, karumbi, no, ['karumbi no', 'no karumib ', ' no karimbi my monkey'])

        # if no primary, then there shouldn't be a secondary match either
        self.validate_categories(poll, None, None, ['yes', 'no'])

        # it no secondary, then there shouldn't be a primary
        self.validate_categories(poll, None, None, ['karimbi'])

        # make sure our response counts add up, one shouldn't have a secondary category
        self.assertEquals(7, PollResponse.objects.filter(category=karumbi).count())
        self.assertEquals(4, PollResponse.objects.filter(category=karumbi, secondary_category=yes).count())
        self.assertEquals(3, PollResponse.objects.filter(category=karumbi, secondary_category=no).count())

        secondary_counts = karumbi.get_secondary_counts()
        self.assertEquals(dict(name=u'yes', count=4, pct=57.1), secondary_counts[yes.id])
        self.assertEquals(dict(name=u'no', count=3, pct=42.8), secondary_counts[no.id])

        secondary_counts = kololo.get_secondary_counts()
        self.assertEquals(dict(name=u'yes', count=4, pct=100.0), secondary_counts[yes.id])
        self.assertEquals(dict(name=u'no', count=0, pct=0), secondary_counts[no.id])

    def test_respondents(self):

        # same number, same respondent
        resp1 = Respondent.get_respondent(get_message(1, 'gorilla'))
        resp2 = Respondent.get_respondent(get_message(1, 'monkey'))
        self.assertEquals(resp1, resp2)
        self.assertEquals(1, Respondent.objects.all().count())

        # new number, different respondent
        resp3 = Respondent.get_respondent(get_message(2, 'monkey'))
        self.assertNotEquals(resp2, resp3)
        self.assertEquals(2, Respondent.objects.all().count())

        # test trac on/off messages
        self.assertEquals("on", resp1.get_active_flag(get_message(1, 'trac on')))
        self.assertEquals("on", resp1.get_active_flag(get_message(1, ' trac on')))
        self.assertEquals("on", resp1.get_active_flag(get_message(1, 'trac oN ')))
        self.assertEquals("off", resp1.get_active_flag(get_message(1, ' TRac off ')))
        self.assertEquals("off", resp1.get_active_flag(get_message(1, ' trAC   off   ')))
        self.assertEquals("off", resp1.get_active_flag(get_message(1, ' Trac   OFF  ')))

        # trac on/off messages should be deliberate, don't let extra characters trigger it
        self.assertEquals(None, resp1.get_active_flag(get_message(1, '.trac on')))
        self.assertEquals(None, resp1.get_active_flag(get_message(1, 'trac on fo sho')))
        self.assertEquals(None, resp1.get_active_flag(get_message(1, ' turn trac on')))

        # set active status returns true when it's changed
        self.assertTrue(resp1.set_active_status(True))

        # trying to set active again, should return false
        self.assertFalse(resp1.set_active_status(True))

        # flipping the bit back to false should return true
        self.assertTrue(resp1.set_active_status(False))

        self.assertTrue(resp1.set_active_status(resp1.get_active_flag(get_message(1, 'trac on')) == "on"))
        self.assertTrue(resp1.set_active_status(resp1.get_active_flag(get_message(1, 'trac off')) == "on"))
        self.assertTrue(resp1.set_active_status(resp1.get_active_flag(get_message(1, 'trac on')) == "on"))
        self.assertFalse(resp1.set_active_status(resp1.get_active_flag(get_message(1, 'trac on')) == "on"))

    def test_analysis(self):

        # create our respondents
        for i in range(1,7):
            Respondent.get_respondent(get_message(i, "respondent"))

        color = self.create_poll(('red', 'green', 'blue'))
        color.process_message(get_message(1, 'red'))
        color.process_message(get_message(2, 'red'))
        color.process_message(get_message(3, 'red'))
        color.process_message(get_message(4, 'green'))
        color.process_message(get_message(5, 'green'))
        color.process_message(get_message(6, 'blue'))

        animal = self.create_poll(('monkey', 'tiger', 'gorilla'))
        animal.process_message(get_message(1, 'monkey'))
        animal.process_message(get_message(2, 'tiger'))
        animal.process_message(get_message(3, 'tiger'))
        animal.process_message(get_message(4, 'gorilla'))
        animal.process_message(get_message(5, 'gorilla'))
        animal.process_message(get_message(6, 'gorilla'))

        query = Respondent.get_queryset((color, animal), dict())

        #for row in query:
        #    print row

    def test_numeric_rules(self):
        
        age = self.create_poll(('#:12', '#13:19', '#20', '#21:60', '#61:'))
        (child, teen, twenty, adult, senior) = age.categories.all()

        self.assertEquals(child, age.process_message(get_message(1, '5')).category)
        self.assertEquals(teen, age.process_message(get_message(2, '13')).category)
        self.assertEquals(twenty, age.process_message(get_message(3, '20')).category)
        self.assertEquals(adult, age.process_message(get_message(4, '60')).category)
        self.assertEquals(senior, age.process_message(get_message(5, '72')).category)

        points = self.create_poll(("#:-5", "#-4:-2", "#-1:"))
        (below_neg5, neg4_to_neg2, above_neg1) = points.categories.all()
        
        self.assertEquals(below_neg5, points.process_message(get_message(1, '-8')).category)
        self.assertEquals(neg4_to_neg2, points.process_message(get_message(2, '-4')).category)
        self.assertEquals(neg4_to_neg2, points.process_message(get_message(3, '-2')).category)
        self.assertEquals(above_neg1, points.process_message(get_message(4, '-1')).category)
        self.assertEquals(above_neg1, points.process_message(get_message(5, '100')).category)

    def test_duplicate_response(self):

        color = self.create_poll(('red', 'green', 'blue'))
        color.start()

        color.process_message(get_message(1, 'red'))
        color.process_message(get_message(1, 'green'))
        color.process_message(get_message(1, 'blue'))

        respondent = Respondent.objects.get(identity=1)

        # should only have one active response and it should be the first one
        responses = respondent.responses.filter(active=True)
        self.assertEquals(1, len(responses))
        self.assertEquals('red', responses[0].message.text)

    def test_unsubscribe(self):

        delay = 0.1
        # we need to sleep after ending polls, etc since auto unsubscribe
        # is based on time-queries. We need to make sure the timestamp advances
        import time

        color = self.create_poll(('red', 'green', 'blue'))
        color.start(); color.end()
        time.sleep(delay)

        # make our respondent active
        message = get_message(1, 'red')
        respondent = Respondent.get_respondent(message)
        respondent.set_active_status(True)
        time.sleep(delay)

        animal = self.create_poll(('monkey', 'tiger', 'gorilla'))
        animal.start(); animal.end()
        time.sleep(delay)

        coffee = self.create_poll(('drip', 'mocha', 'latte'))
        coffee.start(); coffee.end()
        time.sleep(delay)


        # at this point we should still be active since we activated after the first one
        self.assertTrue(Respondent.objects.get(identity=1).active)

        music = self.create_poll(('rock', 'jazz', 'rap'))
        music.start(); music.end()
        time.sleep(delay)

        # it's been three polls, we aren't active anymore
        # feature temporarily disabled Aug 8, 2011
        # self.assertFalse(Respondent.objects.get(connection=1).active)

        # make ourself active again and do the same test
        # only this time, respond to the first poll so we have a last_response
        respondent = Respondent.get_respondent(message)
        respondent.set_active_status(True)
        time.sleep(delay)
        self.assertTrue(Respondent.objects.get(identity=1).active)

        # create a new poll and respond to it
        pet = self.create_poll(('dog', 'cat', 'fish'))
        pet.start()
        time.sleep(delay)
        pet.process_message(get_message(1, 'cat'))
        time.sleep(delay)
        pet.end()
        time.sleep(delay)


        # now two more polls
        condiment = self.create_poll(('mustard', 'ketchup', 'mayonaise'))
        condiment.start(); condiment.end()
        time.sleep(delay)

        snack = self.create_poll(('cracker', 'cheese', 'sausage'))
        snack.start();
        snack.end()
        time.sleep(delay)

        # should still be active, it's only been two polls
        self.assertTrue(Respondent.objects.get(identity=1).active)

        drink = self.create_poll(('water', 'fanta', 'tonic'))
        drink.start(); drink.end()
        time.sleep(delay)

        # third poll should deactivate us
        # feature temporarily disabled Aug 8, 2011
        # self.assertFalse(Respondent.objects.get(connection=1).active)

        color.process_message(message)

    def test_always_updates(self):
        station = self.create_poll(('sanyu', 'wa'))
        station.always_update = True
        station.demographic = True
        station.save()

        animal = self.create_poll(('dog', 'cat', 'fish'))
        animal.keywords.create(name='wa')
        animal.save()
        animal.start()

        color = self.create_poll(('blue', 'green', 'red'))
        color.keywords.create(name='sanyu')
        color.save()
        color.start()

        # respond to the fish message
        message = get_message(1, 'wa fish')
        responses = self.process_message(message)

        # should have two responses, one for our always active poll and our current poll
        self.assertEquals(2, responses.count())

        # check our station is set to wa
        responses = PollResponse.objects.filter(poll=station, respondent=Respondent.get_respondent(message))
        self.assertEquals(1, len(responses))
        self.assertEquals("wa", responses[0].category.name)

        # now respond to our color poll
        message = get_message(1, 'sanyu green')
        responses = self.process_message(message)
        self.assertEquals(3, responses.count())

        # should still have only one response for our station poll, should still read sanyu
        responses = PollResponse.objects.filter(poll=station, respondent=Respondent.get_respondent(message))
        self.assertEquals(1, len(responses))
        self.assertEquals("wa", responses[0].category.name)

        # respond to animal poll a second time
        message = get_message(1, 'wa cat')

        responses = self.process_message(message)
        self.assertEquals(3, responses.count())

    def test_poll_ui(self):
        # without login, we should get redirected
        response = self.client.get(reverse("poll_create"))
        self.assertEquals(302, response.status_code)

        self.assertTrue(self.client.login(username='admin', password='password'))
        response = self.client.get(reverse("poll_create"))
        self.assertEquals(200, response.status_code)

        # should see keywords option and public flag
        self.assertContains(response, "Keywords")
        self.assertContains(response, "Public")

        post_data = response.context['form'].initial
        post_data['name'] = "Test Poll"
        post_data['keywords'] = "test1 test2 test3"
        post_data['description'] = "Test poll description"
        post_data['message'] = "The message to send back"
        post_data['unknown_message'] = "These aren't the droids you're looking for."
        post_data['detailed_chart'] = True
        post_data['is_public'] = True
        post_data['template'] = 0
        post_data['secondary_template'] = 0
        post_data['backend'] = self.backend.id
        response = self.client.post(reverse("poll_create"), post_data)
        self.assertEquals(302, response.status_code)

        # make sure our poll arrived
        poll = Poll.objects.get(name="Test Poll")
        self.assertTrue(poll.is_public)
        self.assertEquals(self.backend, poll.backend)

        # visit the detail page
        response = self.client.get(reverse("poll_view", args=[poll.id]))
        self.assertContains(response, "dataLabels")

        # update the poll to be private
        del post_data['is_public']
        del post_data['detailed_chart']
        response = self.client.post(reverse("poll_edit", args=[poll.id]), post_data)
        self.assertEquals(302, response.status_code)
        poll = Poll.objects.get(name="Test Poll")
        self.assertFalse(poll.is_public)

        response = self.client.get(reverse("poll_view", args=[poll.id]))
        self.assertNotContains(response, "dataLabels")

    def test_respondent_ui(self):

        self.assertTrue(self.client.login(username='admin', password='password'))

        drink = self.create_poll(('water', 'fanta', 'tonic'))
        drink.start()

        occupation = self.create_poll(('farmer', 'politician', 'circus performer', 'droid'))
        occupation.name = "Occupation"
        occupation.demographic = True
        occupation.save()

        name = DemographicQuestion.objects.create(question="Name", created_by=self.user, modified_by=self.user)

        # mmmm... fanta
        message = get_message(1, 'fanta')
        respondent = Respondent.get_respondent(message)
        self.process_message(message)

        # visit the respondent page
        response = self.client.get(reverse("respondent_view", args=[respondent.pk]))
        self.assertContains(response, "fanta")

        # update page
        response = self.client.get(reverse("respondent_edit", args=[respondent.pk]))
        self.assertContains(response, "Name")
        self.assertContains(response, "Occupation")

        droid = PollCategory.objects.get(name="droid")
        response = PollResponse.objects.get(respondent=respondent, poll=occupation)

        post_data = {
            'form-TOTAL_FORMS': u'1',
            'form-INITIAL_FORMS': u'1',
            'form-0-id': response.pk,
            'form-0-category': droid.pk
        }

        post_data['question_%s' % name.pk] = "C3P0"
        self.client.post(reverse("respondent_edit", args=[respondent.pk]), post_data)

        response = self.client.get(reverse("respondent_view", args=[respondent.pk]))
        self.assertContains(response, "C3P0")
        self.assertContains(response, "droid")

    def process_message(self, message):
        poll = Poll.find_poll(message.text, message.connection.backend)
        poll.process_message(message)

        # update the responses for polls that update on every message
        for poll in Poll.objects.filter(demographic=True, always_update=True):
            poll.update_response(message)

        # return all responses ever for this respondent
        respondent = Respondent.get_respondent(message)
        return respondent.responses.all()

    def create_poll(self, categories):
        (user, created) = User.objects.get_or_create(username="test")

        # create a poll off of our template
        poll = Poll.objects.create(name="/".join(categories),
                                   description="simple description",
                                   message="simple message",
                                   backend=self.backend,
                                   user=user)

        for category in categories:
            cat = poll.category_set.categories.create(name=category, message="%s category" % category)
            cat.set_rules(category)
            cat.save()

        return poll



    def validate_categories(self, poll, category, secondary_category, messages):

        phone_number = 1
        try:
            phone_number = globals()["phone_number"]
        except KeyError:
            pass

        for message in messages:
            response = get_response(poll, get_message(phone_number, message))
            self.assertEquals(category, response.category, 'Primary category mismatch for "%s"' % message)
            self.assertEquals(secondary_category, response.secondary_category, 'Secondary category mismatch for "%s"' % message)
            phone_number = phone_number + 1

        globals()["phone_number"] = phone_number

def get_response(poll, message):
    response = poll.process_message(message)
    return PollResponse.objects.get(id=response.id)

def get_message(number, text, backend=None):
    if not backend:
        (backend, created) = Backend.objects.get_or_create(name='test')

    try:
        connection = Connection.objects.get(backend=backend, identity=number)
    except ObjectDoesNotExist:
        connection = Connection.objects.create(backend=backend, identity=number)

    return Message.objects.create(connection=connection, text=text)

def get_rapid_message(number, text, backend=None):
    from rapidsms.messages import IncomingMessage

    db_msg = get_message(number, text)
    msg = IncomingMessage(db_msg.connection, text)
    msg.db_message = db_msg

    return msg
