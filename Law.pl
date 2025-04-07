% =========================================================
% Dynamic Declarations
% =========================================================
:- dynamic
    % Murder Case
    murder/2, age/2, intent/2, premeditated/1,
    used_torture/1, murder_related_to_crime/1, victim_type/2,

    % Negligence Case
    negligent_act/2, circumstance/2,

    % Suicide Cases
    aided_suicide/2, suicide_occurred/2,
    dependent_on/2, used_cruelty/1,

    % Affray Case
    affray_participant/1, group_size/2,
    death_occurred/0, prevented_affray/1.

% =========================================================
% Handle Murder Case (Sections 288-290)
% =========================================================
% murder_case(Person, Victim, PersonAge, Intent, Premeditated, Torture, CrimeRelated, VictimType)
% VictimType can be one of:
%   - ascendant: parent or grandparent of the offender
%   - official: government officer on duty
%   - assistant: someone helping an official
%   - other: none of the above (or unspecified)

handle_case(murder_case(Person, Victim, PersonAge, Intent, Prem, Torture, CrimeRelated, VictimType)) :-
    assertz(murder(Person, Victim)),
    assertz(age(Person, PersonAge)),
    assertz(intent(Person, Intent)),
    ( Prem == true -> assertz(premeditated(Person)) ; true ),
    ( Torture == true -> assertz(used_torture(Person)) ; true ),
    ( CrimeRelated == true -> assertz(murder_related_to_crime(Person)) ; true ),
    ( nonvar(VictimType) -> assertz(victim_type(Victim, VictimType)) ; true ).

% =========================================================
% Handle Negligent Case (Section 291)
% =========================================================
% negligent_case(Person, Victim, PersonAge, Circumstance).
handle_case(negligent_case(Person, Victim, PersonAge, Circumstance)) :-
    assertz(negligent_act(Person, Victim)),
    assertz(age(Person, PersonAge)),
    assertz(circumstance(Person, Circumstance)).

% =========================================================
% Handle Suicide Case by Cruelty (Section 292)
% =========================================================
% suicide_cruelty_case(Person, Victim, PersonAge, VictimAge, SuicideOccurred, Dependent, UsedCruelty).
handle_case(suicide_cruelty_case(Person, Victim, PersonAge, VictimAge, Occurred, Dependent, UsedCruelty)) :-
    assertz(age(Person, PersonAge)),
    assertz(age(Victim, VictimAge)),
    assertz(suicide_occurred(Victim, Occurred)),
    ( Dependent == true -> assertz(dependent_on(Victim, Person)) ; true ),
    ( UsedCruelty == true -> assertz(used_cruelty(Person)) ; true ).

% =========================================================
% Handle Suicide Case by Aiding or Instigation (Section 293)
% =========================================================
% suicide_aid_case(Person, Victim, PersonAge, VictimAge, SuicideOccurred, VictimType)
% VictimType can be one of:
%   - child: under 16 years old
%   - incompetent: unable to understand their actions
%   - uncontrollable: unable to control their actions
handle_case(suicide_aid_case(Person, Victim, PersonAge, VictimAge, Occurred, VictimType)) :-
    assertz(age(Person, PersonAge)),
    assertz(age(Victim, VictimAge)),
    assertz(aided_suicide(Person, Victim)),
    assertz(suicide_occurred(Victim, Occurred)),
    assertz(victim_type(Victim, VictimType)).

% =========================================================
% Handle Group Affray Case (Section 294)
% =========================================================
% affray_case(Person, PersonAge, GroupSize, DeathOccurred, PreventedAffray).
handle_case(affray_case(Person, PersonAge, GroupSize, Death, Prevented)) :-
    assertz(age(Person, PersonAge)),
    assertz(affray_participant(Person)),
    assertz(group_size(Person, GroupSize)),
    ( Death == true -> assertz(death_occurred) ; true ),
    ( Prevented == true -> assertz(prevented_affray(Person)) ; true ).

% =========================================================
% Sentencing Rules (Sections 288–294)
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

% --------- SECTION 292: Suicide due to cruelty toward dependent ---------
sentence(Person, 'up to 7 years and 14,000 Baht fine') :-
    suicide_occurred(Victim, true),
    dependent_on(Victim, Person),
    used_cruelty(Person), !.

% --------- SECTION 293: Aiding/instigating suicide of vulnerable person ---------
sentence(Person, 'up to 5 years or 10,000 Baht fine or both') :-
    aided_suicide(Person, Victim),
    suicide_occurred(Victim, true),
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
