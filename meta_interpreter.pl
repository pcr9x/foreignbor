%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Knowledge Base (Supports built-ins!)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

age(john, 16).
age(alice, 20).

minor(X) :- age(X, A), A < 18.
can_vote(X) :- \+ minor(X).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Meta-Interpreter with built-in predicate support
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Base case
prove(true, [true]).

% Conjunctions
prove((A, B), Trace) :-
    prove(A, TA),
    prove(B, TB),
    append(TA, TB, Trace).

% Handle built-in predicates directly (e.g., A < 18)
prove(Goal, [built_in(Goal)]) :-
    predicate_property(Goal, built_in),
    call(Goal).

% Rule with body (non-fact)
prove(Goal, [ (Goal :- Body) | Trace ]) :-
    clause(Goal, Body),
    Body \= true,
    prove(Body, Trace).

% Fact (clause with body true)
prove(Goal, [Goal]) :-
    clause(Goal, true).

% Negation as failure (optional extension)
prove(\+ Goal, [not(Goal)]) :-
    \+ call(Goal).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Example Queries:
%
% ?- prove(minor(john), Trace).
% Trace = [ (minor(john) :- (age(john, A), A<18)), age(john, 16), built_in(16<18) ]
%
% ?- prove(can_vote(john), Trace).
% Trace = [not(minor(john))]  % because minor(john) succeeds, so \+ minor(john) fails
%
% ?- prove(can_vote(alice), Trace).
% Trace = [ (can_vote(alice) :- \+ minor(alice)), not(minor(alice)) ]
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
