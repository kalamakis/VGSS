%% -----------------------------
%% Conductor C1 (Bottom Blue Box)
%% 6 faces, each with 4 corners
C1 = [
% FRONT
-2 -1 0    -2  1 0    -2  1 1   -2 -1 1;
% BACK
2 -1 0     2  1 0     2  1 1    2 -1 1;
% LEFT
-2  1 0     2  1 0     2  1 1   -2  1 1;
% RIGHT
-2 -1 0     2 -1 0     2 -1 1   -2 -1 1;
% BOTTOM
-2 -1 0     2 -1 0     2  1 0   -2  1 0;
% TOP
-2 -1 1     2 -1 1     2  1 1   -2  1 1
];

%% -----------------------------
%% Conductor C2 (Top Red Tilted Box)
C2 = [
% BACK
2 -0.866 2.5   2  0.866 3.5   2  0.866 4.5   2 -0.866 3.5;
% FRONT
-2 -0.866 2.5  -2  0.866 3.5  -2  0.866 4.5  -2 -0.866 3.5;
% LEFT
-2  0.866 3.5   2  0.866 3.5   2  0.866 4.5  -2  0.866 4.5;
% RIGHT
-2 -0.866 2.5   2 -0.866 2.5   2 -0.866 3.5  -2 -0.866 3.5;
% BOTTOM
-2 -0.866 2.5   2 -0.866 2.5   2  0.866 3.5  -2  0.866 3.5;
% TOP
-2 -0.866 3.5   2 -0.866 3.5   2  0.866 4.5  -2  0.866 4.5
];

%% -----------------------------
%% Dielectric Panel (Green)
% 4 corners, flat panel between C1 and C2
%D1 = [
%-1.5  -0.8  2  1.5  -0.8  2   1.5   0.8  2   -1.5   0.8  2
%];

%% -----------------------------
%% Plotting
%figure
%hold on
%axis equal
%grid on
%view(3)
%xlabel('X')
%ylabel('Y')
%zlabel('Z')
%title('3D Conductors with Dielectric Panel')

%% Draw C1 (Blue)
%for i = 1:6
    %face = reshape(C1(i,:),3,4)';
   % patch(face(:,1),face(:,2),face(:,3),'blue','FaceAlpha',0.4)
%end

%% Draw C2 (Red Tilted)
%for i = 1:6
  %  face = reshape(C2(i,:),3,4)';
   % patch(face(:,1),face(:,2),face(:,3),'red','FaceAlpha',0.4)
%end

%% Draw Dielectric Panel (Green)
%face = reshape(D1,3,4)';  % 4 corners × 3 coordinates
%patch(face(:,1),face(:,2),face(:,3),'green','FaceAlpha',0.5)

%% Legend
%legend('C1','C2','Dielectric')