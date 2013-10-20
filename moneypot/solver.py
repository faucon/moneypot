#coding: utf-8
'''
This Module contains different Solver strategies

Solvers return list of tuples which represent payments:
    (participant_from, participant_to, amount)
'''


class MatchingSolver(object):
    '''
    This solver tries to match amounts
    if this doesn't work the participants with highest debts has to receive and distribute the payments
    (he has paid less - but he has now more to do)
    '''

    def solve(self, pot):
        '''
        the actual solve method
        it takes the following steps:
            - sort participants in paying and receiving participants
            - try to match participants with opposed result (one paying
            participant has to pay exactely the amount another participant has to receive)

            - for the rest: all paying participants pay to the one participant
            who has the most debts
            - this participants has to distribute the money
        '''
        participants_done = []
        participants_pay = []
        participants_receive = []

        payments = []

        for p in pot.participants:
            if p.result == 0:       # this is good, nothing to do for this participant
                participants_done.append(p)
            elif p.result > 0:      # positive result: p will get money
                participants_receive.append(p)
            else:   # if nothing from the above he has to pay something
                participants_pay.append(p)

        #this looks like quadratic runtime scaling,
        #but I don't think this will be a problem for the actual number of participants
        for p in participants_pay:
            for possible_receiver in participants_receive:
                if p.result == -possible_receiver.result:
                    #if match found, create a payment, remove receiver from open list
                    #stop this loop
                    payment = (p, possible_receiver, possible_receiver.result)
                    payments.append(payment)
                    participants_receive.remove(possible_receiver)
                    participants_done.append(p)
                    participants_done.append(possible_receiver)
                    break

        #TODO: not matched payments
        return payments
