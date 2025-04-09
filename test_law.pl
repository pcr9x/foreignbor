% to run enter "swipl" in the terminal and make sure law.pl and test_law.pl are in the same dir
% run "[test_law]." and "run_tests."

:- begin_tests(law).
:- consult('Law.pl').

% Existing Tests
test(section_295_basic_injury) :-
    clear_case,
    handle_case(injury_case(john, mark, true, true, true, false, false, false, false, other, false)),
    sentence(john, Sentence),
    Sentence == 'up to 2 years or 4,000 Baht fine or both'.

test(section_295_attempted) :-
    clear_case,
    handle_case(injury_case(jane, jack, true, false, true, false, false, false, false, other, false)),
    sentence(jane, Sentence),
    Sentence == 'up to 1 year or 1,300 Baht fine or both (attempted)'.

test(section_298_grievous_aggravated) :-
    clear_case,
    handle_case(injury_case(alex, bob, true, true, true, true, true, true, false, official, false)),
    sentence(alex, Sentence),
    Sentence == '2 to 10 years imprisonment'.

test(section_288_murder_unaggravated) :-
    clear_case,
    handle_case(murder_case(frank, george, true, true, false, false, false, other, true, false)),
    sentence(frank, Sentence),
    Sentence == '15-20 years imprisonment'.

test(section_289_murder_aggravated) :-
    clear_case,
    handle_case(murder_case(steve, lucas, true, true, true, true, false, official, true, false)),
    sentence(steve, Sentence),
    Sentence == 'Death'.

test(section_290_unintentional_aggravated) :-
    clear_case,
    handle_case(murder_case(anna, sam, true, false, false, true, false, ascendant, true, false)),
    sentence(anna, Sentence),
    Sentence == '3-20 years imprisonment (aggravated injury)'.

test(section_291_negligent_death) :-
    clear_case,
    handle_case(negligent_case(david, max, true, false, true)),
    sentence(david, Sentence),
    Sentence == 'not more than 10 years imprisonment or 20,000 Baht fine'.

test(section_292_suicide_cruelty) :-
    clear_case,
    handle_case(suicide_cruelty_case(tom, jerry, true, true, true, true)),
    sentence(tom, Sentence),
    Sentence == 'up to 7 years and 14,000 Baht fine'.

test(section_293_suicide_aid_child) :-
    clear_case,
    handle_case(suicide_aid_case(kate, emily, true, true, child)),
    sentence(kate, Sentence),
    Sentence == 'up to 5 years or 10,000 Baht fine or both'.

test(section_294_affray_death) :-
    clear_case,
    handle_case(affray_case(chris, true, true, false, false)),
    sentence(chris, Sentence),
    Sentence == 'up to 2 years or 4,000 Baht fine or both'.

test(section_299_affray_grievous) :-
    clear_case,
    handle_case(affray_case(luke, true, false, false, true)),
    sentence(luke, Sentence),
    Sentence == 'up to 1 year or 2,000 Baht fine or both'.

test(self_defense_case) :-
    clear_case,
    handle_case(injury_case(ray, max, true, true, true, false, false, false, false, other, true)),
    sentence(ray, Sentence),
    Sentence == "if the act committed is in excess of what is reasonable under the circumstances or in excess of what is necessary, or in excess of what is necessary for the defense, the Court may inflict less punishment to any extent than that provided by the law for such offence. But, if such act occurs out of excitement, fright or fear, the Court may not inflict any punishment at all.".

test(underage_case) :-
    clear_case,
    handle_case(injury_case(tim, tom, false, true, true, false, false, false, false, other, false)),
    sentence(tim, Sentence),
    Sentence == "The Court shall take into account the sense of responsibility and all other things concerning such person in order to come to decision as to whether it is expedient to pass judgment inflicting punishment on such person or not.".

test(murder_attempt_aggravated) :-
    clear_case,
    handle_case(murder_case(ben, vic, true, true, true, false, false, ascendant, false, false)),
    sentence(ben, Sentence),
    Sentence == 'Life time imprisonment (attempted)'.

test(negligent_grievous_no_death) :-
    clear_case,
    handle_case(negligent_case(amy, bob, true, true, false)),
    sentence(amy, Sentence),
    Sentence == 'up to 3 years or 6,000 Baht fine or both'.

test(suicide_aid_nonvulnerable) :-
    clear_case,
    handle_case(suicide_aid_case(kim, lynn, true, true, other)),
    \+ sentence(kim, _).

:- end_tests(law).
