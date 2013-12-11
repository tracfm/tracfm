from django.db import models
from simple_locations.models import Area
import re

class Area (Area):
    """ Extend simple_location Area to have aliases """

    def __init__(self, *args, **kwargs):
        self._rules = None
        super(Area, self).__init__(*args, **kwargs)

    def get_rules(self):
        """ Get the aliases as lines. """
        return "\n".join([rule.match for rule in self.rules.all()])

    def set_rules(self, rules):
        self._rules = rules

    def save(self, **kwargs):
        """
        We overload our save to set/update any aliases after we are committed.
        """
        # save away
        super(Area, self).save(**kwargs)

        # now also save our rules if they are present
        rules = getattr(self, '_rules', None)
        if not rules is None:

            # remove our existing rules
            self.rules.all().delete()

            # and set our new ones
            for rule in rules.splitlines():
                self.rules.create(match=rule, area=self)


class AreaRule(models.Model):
    """ A rule for matching an area """
    area = models.ForeignKey(Area, related_name="rules")    
    match = models.CharField(max_length=65)
    order = models.IntegerField(default=0)

    def matches(self, message, fuzzy=False):
        """
        Returns whether this rule matches the passed in message.  The 'fuzzy' attribute
        marks whether any edit distance will be taken into account when matching
        """
        raw = message.lower()
        raw = re.sub("[^0-9a-z]", " ", raw)
        raw = raw.split()

        matches = self.match.lower()
        matches = re.sub("[^0-9a-z]", " ", matches)
        matches = matches.split()

        # see if each of our matches is present
        scores = [match in raw for match in matches]

        # we need to match all our matches
        matched = not False in scores

        # if we are doing fuzzy, try that
        if not matched and fuzzy:
            scores = []
            for match in matches:
                match_scores = [edit_distance(word, match) <= 1 for word in raw]
                scores.append(True in match_scores)
            matched = not False in scores

        return matched
    

def edit_distance(s1, s2):
    """
    Compute the Damerau-Levenshtein distance between two given
    strings (s1 and s2)
    """
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in xrange(-1,lenstr1+1):
        d[(i,-1)] = i+1
    for j in xrange(-1,lenstr2+1):
        d[(-1,j)] = j+1
 
    for i in xrange(0,lenstr1):
        for j in xrange(0,lenstr2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i,j)] = min(
                           d[(i-1,j)] + 1, # deletion
                           d[(i,j-1)] + 1, # insertion
                           d[(i-1,j-1)] + cost, # substitution
                          )
            if i>1 and j>1 and s1[i]==s2[j-1] and s1[i-1] == s2[j]:
                d[(i,j)] = min (d[(i,j)], d[i-2,j-2] + cost) # transposition
 
    return d[lenstr1-1,lenstr2-1]
