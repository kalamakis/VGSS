%% ================================================================
%% TEST INPUT: DIRECTLY TOUCHING CONDUCTORS
%%
%% Purpose:
%%   - C1 touches C2 directly at x = 1.
%%   - C2 touches C3 directly at x = 2.
%%   - C1 does NOT touch C3.
%%
%% Expected behavior when master = C1:
%%   - Ignore C2 because it directly touches C1.
%%   - Still take C3 into account.
%%   - dPX(C1, C3) = xmin(C3) - xmax(C1) = 2 - 1 = 1
%%   - Initial D[PX] = 1 / 2 = 0.5
%%
%% Additional non-touching conductors:
%%   - C4 constrains PY for C1.
%%   - C5 constrains NX for C1.
%% ================================================================

%% ================================================================
%% CONDUCTOR C1  —  box  (0,0,0) → (1,1,1)  |  eps_r = 3
%% ================================================================
C1 = [
    0   0   0     0   1   0     1   1   0     1   0   0 ;  % Face 1: Bottom  z=0
    0   0   1     1   0   1     1   1   1     0   1   1 ;  % Face 2: Top     z=1
    0   0   0     1   0   0     1   0   1     0   0   1 ;  % Face 3: Front   y=0
    0   1   0     0   1   1     1   1   1     1   1   0 ;  % Face 4: Back    y=1
    0   0   0     0   0   1     0   1   1     0   1   0 ;  % Face 5: Left    x=0
    1   0   0     1   1   0     1   1   1     1   0   1 ;  % Face 6: Right   x=1
];

%% ================================================================
%% CONDUCTOR C2  —  box  (1,0,0) → (2,1,1)  |  eps_r = 4
%% Directly touches C1 at the face x = 1
%% ================================================================
C2 = [
    1   0   0     1   1   0     2   1   0     2   0   0 ;  % Face 1: Bottom  z=0
    1   0   1     2   0   1     2   1   1     1   1   1 ;  % Face 2: Top     z=1
    1   0   0     2   0   0     2   0   1     1   0   1 ;  % Face 3: Front   y=0
    1   1   0     1   1   1     2   1   1     2   1   0 ;  % Face 4: Back    y=1
    1   0   0     1   0   1     1   1   1     1   1   0 ;  % Face 5: Left    x=1
    2   0   0     2   1   0     2   1   1     2   0   1 ;  % Face 6: Right   x=2
];

%% ================================================================
%% CONDUCTOR C3  —  box  (2,0,0) → (3,1,1)  |  eps_r = 5
%% Directly touches C2 at x = 2, but does NOT directly touch C1
%% ================================================================
C3 = [
    2   0   0     2   1   0     3   1   0     3   0   0 ;  % Face 1: Bottom  z=0
    2   0   1     3   0   1     3   1   1     2   1   1 ;  % Face 2: Top     z=1
    2   0   0     3   0   0     3   0   1     2   0   1 ;  % Face 3: Front   y=0
    2   1   0     2   1   1     3   1   1     3   1   0 ;  % Face 4: Back    y=1
    2   0   0     2   0   1     2   1   1     2   1   0 ;  % Face 5: Left    x=2
    3   0   0     3   1   0     3   1   1     3   0   1 ;  % Face 6: Right   x=3
];

%% ================================================================
%% CONDUCTOR C4  —  box  (0,3,0) → (1,4,1)  |  eps_r = 6
%% Non-touching conductor that constrains PY for C1
%% ================================================================
C4 = [
    0   3   0     0   4   0     1   4   0     1   3   0 ;  % Face 1: Bottom  z=0
    0   3   1     1   3   1     1   4   1     0   4   1 ;  % Face 2: Top     z=1
    0   3   0     1   3   0     1   3   1     0   3   1 ;  % Face 3: Front   y=3
    0   4   0     0   4   1     1   4   1     1   4   0 ;  % Face 4: Back    y=4
    0   3   0     0   3   1     0   4   1     0   4   0 ;  % Face 5: Left    x=0
    1   3   0     1   4   0     1   4   1     1   3   1 ;  % Face 6: Right   x=1
];

%% ================================================================
%% CONDUCTOR C5  —  box  (-4,0,0) → (-3,1,1)  |  eps_r = 7
%% Non-touching conductor that constrains NX for C1
%% ================================================================
C5 = [
   -4   0   0    -4   1   0    -3   1   0    -3   0   0 ;  % Face 1: Bottom  z=0
   -4   0   1    -3   0   1    -3   1   1    -4   1   1 ;  % Face 2: Top     z=1
   -4   0   0    -3   0   0    -3   0   1    -4   0   1 ;  % Face 3: Front   y=0
   -4   1   0    -4   1   1    -3   1   1    -3   1   0 ;  % Face 4: Back    y=1
   -4   0   0    -4   0   1    -4   1   1    -4   1   0 ;  % Face 5: Left    x=-4
   -3   0   0    -3   1   0    -3   1   1    -3   0   1 ;  % Face 6: Right   x=-3
];
