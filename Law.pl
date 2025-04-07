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
    affray_participant/1,
    death_occurred/0, prevented_affray/1,

    % Injury Cases
    harm/2, grievous_injury/2.

% =========================================================
% Handle Injury Case (Sections 295-298)
% =========================================================
% injury_case(Person, Victim, PersonAge, Grievous, Premeditated, Torture, CrimeRelated, VictimType)
% CrimeRelated = Have a purpose of securing the benefit obtained through the other offence, or concealing the other offence or escaping punishment for the other offence committed by him
% VictimType can be:
%   - ascendant
%   - official
%   - assistant
%   - other
handle_case(injury_case(Person, Victim, PersonAge, Grievous, Prem, Torture, CrimeRelated, VictimType)) :-
    assertz(harm(Person, Victim)),
    assertz(age(Person, PersonAge)),
    ( Grievous == true -> assertz(grievous_injury(Person, Victim)) ; true ),
    ( Prem == true -> assertz(premeditated(Person)) ; true ),
    ( Torture == true -> assertz(used_torture(Person)) ; true ),
    ( CrimeRelated == true -> assertz(murder_related_to_crime(Person)) ; true ),
    ( nonvar(VictimType) -> assertz(victim_type(Victim, VictimType)) ; true ).


% =========================================================
% Handle Murder Case (Sections 288-290)
% =========================================================
% murder_case(Person, Victim, PersonAge, Intent, Premeditated, Torture, CrimeRelated, VictimType)
% CrimeRelated = Have a purpose of securing the benefit obtained through the other offence, or concealing the other offence or escaping punishment for the other offence committed by him
% VictimType can be:
%   - ascendant
%   - official
%   - assistant
%   - other
handle_case(murder_case(Person, Victim, PersonAge, Intent, Prem, Torture, CrimeRelated, VictimType)) :-
    assertz(murder(Person, Victim)),
    assertz(age(Person, PersonAge)),
    assertz(intent(Person, Intent)),
    ( Prem == true -> assertz(premeditated(Person)) ; true ),
    ( Torture == true -> assertz(used_torture(Person)) ; true ),
    ( CrimeRelated == true -> assertz(murder_related_to_crime(Person)) ; true ),
    ( nonvar(VictimType) -> assertz(victim_type(Victim, VictimType)) ; true ).

% =========================================================
% Handle Negligent Case (Section 291, 300)
% =========================================================
% negligent_case(Person, Victim, PersonAge, Circumstance, GrievousInjury, CausedDeath)
handle_case(negligent_case(Person, Victim, PersonAge, Circumstance, Grievous, Death)) :-
    assertz(negligent_act(Person, Victim)),
    assertz(age(Person, PersonAge)),
    assertz(circumstance(Person, Circumstance)),
    ( Grievous == true -> assertz(grievous_injury(Person, Victim)) ; true ),
    ( Death == true -> assertz(death_occurred) ; true ).

% =========================================================
% Handle Suicide Case by Cruelty (Section 292)
% =========================================================
% suicide_cruelty_case(Person, Victim, PersonAge, VictimAge, SuicideOccurred, Dependent, UsedCruelty)
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
% VictimType can be:
%   - child
%   - incompetent
%   - uncontrollable
handle_case(suicide_aid_case(Person, Victim, PersonAge, VictimAge, Occurred, VictimType)) :-
    assertz(age(Person, PersonAge)),
    assertz(age(Victim, VictimAge)),
    assertz(aided_suicide(Person, Victim)),
    assertz(suicide_occurred(Victim, Occurred)),
    assertz(victim_type(Victim, VictimType)).

% =========================================================
% Handle Group Affray Case (Section 294, 299)
% =========================================================
% affray_case(Person, PersonAge, DeathOccurred, PreventedAffray, GrievousInjury)
handle_case(affray_case(Person, PersonAge, Death, Prevented, Grievous)) :-
    assertz(age(Person, PersonAge)),
    assertz(affray_participant(Person)),
    ( Death == true -> assertz(death_occurred) ; true ),
    ( Prevented == true -> assertz(prevented_affray(Person)) ; true ),
    ( Grievous == true -> assertz(grievous_injury(Person, victim)) ; true ).

% =========================================================
% Sentencing Rules (Sections 288-294)
% =========================================================

% --------- SECTION 295: Basic Bodily Harm ---------
sentence(Person, 'up to 2 years or 4,000 Baht fine or both') :-
    harm(Person, _),
    \+ (
        premeditated(Person)
        ; used_torture(Person)
        ; murder_related_to_crime(Person)
        ; victim_type(_, ascendant)
        ; victim_type(_, official)
        ; victim_type(_, assistant)
    ), !.

% --------- SECTION 296: Bodily Harm with Section 289 circumstances ---------
sentence(Person, 'not more than 3 years or 6,000 Baht fine or both') :-
    harm(Person, _),
    \+ grievous_injury(Person, _),
    (
        premeditated(Person)
        ; used_torture(Person)
        ; murder_related_to_crime(Person)
        ; victim_type(_, ascendant)
        ; victim_type(_, official)
        ; victim_type(_, assistant)
    ), !.

% --------- SECTION 297: Grievous Bodily Harm ---------
sentence(Person, '6 months to 10 years imprisonment') :-
    grievous_injury(Person, _),
    \+ (
        premeditated(Person)
        ; used_torture(Person)
        ; murder_related_to_crime(Person)
        ; victim_type(_, ascendant)
        ; victim_type(_, official)
        ; victim_type(_, assistant)
    ), !.

% --------- SECTION 298: Grievous + Aggravated ---------
sentence(Person, '2 to 10 years imprisonment') :-
    grievous_injury(Person, _),
    (
        premeditated(Person)
        ; used_torture(Person)
        ; murder_related_to_crime(Person)
        ; victim_type(_, ascendant)
        ; victim_type(_, official)
        ; victim_type(_, assistant)
    ), !.

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

% --------- SECTION 300: Negligent Grievous Injury ---------
sentence(Person, 'up to 3 years or 6,000 Baht fine or both') :-
    negligent_act(Person, Victim),
    grievous_injury(Person, Victim),
    \+ death_occurred, !.

% --------- SECTION 291: Negligent Causing Death ---------
sentence(Person, 'not more than 10 years imprisonment or 20,000 Baht fine') :-
    negligent_act(Person, _),
    death_occurred,
    \+ grievous_injury(Person, _), !.

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

% --------- SECTION 299: Affray Causing Grievous Injury ---------
sentence(Person, 'up to 1 year or 2,000 Baht fine or both') :-
    affray_participant(Person),
    \+ death_occurred,
    grievous_injury(_, _),
    \+ prevented_affray(Person), !.

% =========================================================
% Utility: Clear all asserted case data
% =========================================================
clear_case :-
    retractall(murder(_, _)),
    retractall(age(_, _)),
    retractall(intent(_, _)),
    retractall(premeditated(_)),
    retractall(used_torture(_)),
    retractall(murder_related_to_crime(_)),
    retractall(victim_type(_, _)),
    retractall(negligent_act(_, _)),
    retractall(circumstance(_, _)),
    retractall(aided_suicide(_, _)),
    retractall(suicide_occurred(_, _)),
    retractall(dependent_on(_, _)),
    retractall(used_cruelty(_)),
    retractall(affray_participant(_)),
    retractall(prevented_affray(_)),
    retractall(death_occurred),
    retractall(harm(_, _)),
    retractall(grievous_injury(_, _)).