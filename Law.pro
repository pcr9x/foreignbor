murder(intentional, Punishment) :-
    Punishment = death;
    Punishment = 15-20.

murder(aggravated(Circumstance), Punishment) :-
    member(Circumstance, [
        ascendant,
        official_in_function,
        assisting_official,
        premeditation,
        torture_or_cruelty,
        facilitating_other_offence,
        securing_benefit_or_concealing_offence
    ]),
    Punishment = death.

murder(unintentional, Punishment) :-
    Punishment = imprisonment(3, 15).

murder(unintentional_aggravated, Punishment) :-
    Punishment = imprisonment(3, 20).

murder(negligent, Punishment) :-
    Punishment = imprisonment(0, 10);
    Punishment = fine(0, 20000).