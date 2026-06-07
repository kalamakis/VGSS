%% -----------------------------
%% Trapezoid 1 (Bottom Blue)
%C1_faces = struct();

% Front Face
%C1_faces.Front  = [
   C1 = [ 
       -2   0   0   2   0   0    2   0   1     -2   0   1;

% Back Face
%C1_faces.Back   = [
   
    -1   3   0     1   3   0       1   3   1      -1   3   1;

% Left Face
%C1_faces.Left   = [
    -2   0   0     -1   3   0      -1   3   1     -2   0   1;

% Right Face
%C1_faces.Right  = [
     2   0   0     1   3   0       1   3   1       2   0   1;

% Bottom Face
%C1_faces.Bottom = [
    -2   0   0     2   0   0       1   3   0      -1   3   0;

% Top Face
%C1_faces.Top    = [
    -2   0   1     2   0   1        1   3   1     -1   3   1
    ];

%% -----------------------------
%% Trapezoid 2 (Top Red, shifted)
%C2_faces = struct();

% Front Face
%C2_faces.Front  = [
 C2 = [
 %-1.75   0.5    0       1.75   0.5    0     1.75   0.5    1   -1.75   0.5    1;

% Back Face
%C2_faces.Back   = [
   -0.75   3.5    0    0.75   3.5    0      0.75   3.5    1   -0.75   3.5    1;

% Left Face
%C2_faces.Left   = [
   -1.75   0.5    0    -0.75   3.5    0    -0.75   3.5    1    -1.75   0.5    1;

% Right Face
%C2_faces.Right  = [
    1.75   0.5    0     0.75   3.5    0    0.75   3.5    1    1.75   0.5    1;

% Bottom Face
%C2_faces.Bottom = [
   -1.75   0.5    0      1.75   0.5    0     0.75   3.5    0   -0.75   3.5    0;
%];

% Top Face
%C2_faces.Top    = [
   -1.75   0.5    1      1.75   0.5    1      0.75   3.5    1    -0.75   3.5    1
];

%% -----------------------------
%% Dielectric Panel (Green)
D1 = [
   -1   -0.5   1    1   -0.5   1    1    0.5   1   -1    0.5   1];