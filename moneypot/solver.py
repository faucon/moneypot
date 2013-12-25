#coding: utf-8
'''
This Module contains different Solver strategies

Solvers return list of tuples which represent payments:
    (participant_from, participant_to, amount)
'''

import itertools


class MatchingSolver(object):
    '''
    This solver tries to match amounts
    if this doesn't work the participants with highest debts has to receive and distribute the payments
    (he has paid less - but he has now more to do)
    '''

    def __init__(self, pot):
        '''
        init solver: take a pot
            - sort participants in paying and receiving participants
        '''
        self.pot = pot
        self.participants_done = []
        self.participants_open = []

        self.payments = []

        for p in self.pot.participants:
            if p.result == 0:       # this is good, nothing to do for this participant
                self.participants_done.append(p)
            else:
                self.participants_open.append(p)

    def pairmatching(self):
        #look at all pairs, if their results sum up to 0 we found a good pair
        for p1, p2 in itertools.combinations(self.participants_open, 2):
            if p1.result + p2.result == 0:
                if p1.result < 0:
                    payer = p1
                    receiver = p2
                else:
                    payer = p2
                    receiver = p1
                payment = (payer, receiver, receiver.result)
                self.payments.append(payment)
                self.participants_open.remove(p1)
                self.participants_open.remove(p2)
                self.participants_done.append(p1)
                self.participants_done.append(p2)
                break

    def triangular_helper(self, p, q):
        '''
        look at two participants p and q
        if they have different signs in their results (i.e. one has to pay the other will receive)
        create a payment from payer to receiver with the smaller absolute amount and add it to the payment list
        '''
        if cmp(p.result, 0) != cmp(q.result, 0):            # cmp(x,0) is like sign(x)
            amount = min([abs(p.result), abs(q.result)])
            if p.result < 0:
                payment = (p, q, amount)
            else:
                payment = (q, p, amount)
            self.payments.append(payment)

    def triangularmatching(self):
        #look at all three-pairs if they would sum up to 0

        for p1, p2, p3 in itertools.combinations(self.participants_open, 3):
            if p1.result + p2.result + p3.result == 0:
                #check all pairs
                for (p, q) in itertools.combinations([p1, p2, p3], 2):
                    self.triangular_helper(p, q)

    def solve(self):
        '''
        the actual solve method
            - try to match participants with opposed result (one paying
            participant has to pay exactely the amount another participant has to receive)

            try to match triangular matchings (one receiver will get exactly what two others have to pay or the other way round)

            - for the rest: all paying participants pay to the one participant
            who has the most debts
            - this participants has to distribute the money
        '''

        self.pairmatching()
        self.triangularmatching()

        #TODO: not matched payments
        return self.payments
