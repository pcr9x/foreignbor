%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Base Data
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

base_price(tshirt, 100).

student(alice).
has_coupon(alice).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Modifier Definitions (named)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

modifier(student_discount, Person, PriceIn, PriceOut) :-
    student(Person),
    PriceOut is PriceIn * 0.8.

modifier(coupon_discount, Person, PriceIn, PriceOut) :-
    has_coupon(Person),
    PriceOut is max(0, PriceIn - 10).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Final Price Logic: Apply each modifier once
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% List all modifier names here
modifier_list([student_discount, coupon_discount]).

final_price(Person, Item, FinalPrice) :-
    base_price(Item, BasePrice),
    modifier_list(Modifiers),
    apply_modifiers_once(Person, BasePrice, Modifiers, FinalPrice).

% Apply modifiers one by one, skipping used ones
apply_modifiers_once(_, Price, [], Price).

apply_modifiers_once(Person, PriceIn, [ModName | Rest], PriceOut) :-
    ( modifier(ModName, Person, PriceIn, TempPrice)
      -> true
      ;  TempPrice = PriceIn  % no change if not applicable
    ),
    apply_modifiers_once(Person, TempPrice, Rest, PriceOut).
