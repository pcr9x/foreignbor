% =========================================================
% Dynamic Declarations
% =========================================================
:- dynamic
    % Murder Case
    murder/2, age/2, intent/2, premeditated/1,
    used_torture/1, murder_related_to_crime/1, victim_type/2,

    % Negligence Case
    negligent_act/2, circumstance/2,

    % Suicide Case
    aided_suicide/2, suicide_occurred/2,

    % Affray Case
    affray_participant/1, group_size/2,
    death_occurred/0, prevented_affray/1.

% =========================================================
% Handle Murder Case (Sections 288-290)
% =========================================================
% murder_case(Person, Victim, Age, Intent, Premeditated, Torture, CrimeRelated, VictimType).
% VictimType: ascendant / official / assistant / other

handle_case(murder_case(Person, Victim, Age, Intent, Prem, Torture, CrimeRelated, VictimType)) :-
    assertz(murder(Person, Victim)),
    assertz(age(Person, Age)),
    assertz(intent(Person, Intent)),
    ( Prem == yes -> assertz(premeditated(Person)) ; true ),
    ( Torture == yes -> assertz(used_torture(Person)) ; true ),
    ( CrimeRelated == yes -> assertz(murder_related_to_crime(Person)) ; true ),
    ( nonvar(VictimType) -> assertz(victim_type(Victim, VictimType)) ; true ).

% =========================================================
% Handle Negligent Case (Section 291)
% =========================================================
% negligent_case(Person, Victim, Age, Circumstance).
handle_case(negligent_case(Person, Victim, Age, Circumstance)) :-
    assertz(negligent_act(Person, Victim)),
    assertz(age(Person, Age)),
    assertz(circumstance(Person, Circumstance)).

% =========================================================
% Handle Suicide-Related Case (Section 293)
% =========================================================
% suicide_case(Person, Victim, Age, SuicideOccurred, VictimType).
% VictimType: child / incompetent / uncontrollable
handle_case(suicide_case(Person, Victim, Age, Occurred, VictimType)) :-
    assertz(aided_suicide(Person, Victim)),
    assertz(age(Person, Age)),
    assertz(suicide_occurred(Victim, Occurred)),
    assertz(victim_type(Victim, VictimType)).

% =========================================================
% Handle Group Affray Case (Section 294)
% =========================================================
% affray_case(Person, GroupSize, DeathOccurred, PreventedAffray).
handle_case(affray_case(Person, GroupSize, Death, Prevented)) :-
    assertz(affray_participant(Person)),
    assertz(group_size(Person, GroupSize)),
    ( Death == yes -> assertz(death_occurred) ; true ),
    ( Prevented == yes -> assertz(prevented_affray(Person)) ; true ).

% =========================================================
% Sentencing Rules
% =========================================================

% --------- SECTION 289: AGGRAVATED MURDER ---------
sentence(Person, death) :-
    murder(Person, Victim),
    intent(Person, true),
    (
        premeditated(Person)
        ; used_torture(Person)
        ; murder_related_to_crime(Person)
        ; victim_type(Victim, ascendant)
        ; victim_type(Victim, official)
        ; victim_type(Victim, assistant)
    ), !.

% --------- SECTION 288: MURDER WITHOUT AGGRAVATION ---------
sentence(Person, '15-20 years imprisonment') :-
    murder(Person, _),
    intent(Person, true), !.

% --------- SECTION 290: UNINTENTIONAL KILLING (INJURY CAUSED DEATH) ---------
sentence(Person, '3-20 years imprisonment (aggravated injury)') :-
    murder(Person, Victim),
    intent(Person, false),
    (
        premeditated(Person)
        ; used_torture(Person)
        ; murder_related_to_crime(Person)
        ; victim_type(Victim, ascendant)
        ; victim_type(Victim, official)
        ; victim_type(Victim, assistant)
    ), !.

sentence(Person, '3-15 years imprisonment') :-
    murder(Person, _),
    intent(Person, false), !.

% --------- SECTION 291: NEGLIGENCE ---------
sentence(Person, 'up to 10 years imprisonment or 20,000 Baht fine') :-
    negligent_act(Person, _), !.

% --------- SECTION 293: AIDING/INSTIGATING SUICIDE ---------
sentence(Person, 'up to 5 years or 10,000 Baht fine or both') :-
    aided_suicide(Person, Victim),
    suicide_occurred(Victim, yes),
    (
        victim_type(Victim, child)
        ; victim_type(Victim, incompetent)
        ; victim_type(Victim, uncontrollable)
    ), !.

% --------- SECTION 294: AFFRAY RESULTING IN DEATH ---------
sentence(Person, none) :-
    prevented_affray(Person), !.

sentence(Person, 'up to 2 years or 4,000 Baht fine or both') :-
    affray_participant(Person),
    death_occurred, !.
