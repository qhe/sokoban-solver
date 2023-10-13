# sokoban-solver
Simple brute force sokoban solver

Playing sokoban with kid, got stuck, decided to write a solver

### how it works

brute force DFS based on frames

A frame is a combination of box positions and reachable cells by the character. The exact character position is insignificant.
It's considered an invalid frame and not being searched if any box is in dead corners (a non-goal cell having two adjacent walls)

Since we are searching based on frames, only box movement are interesting, character movement is trivial and can be easily filled in once a solution is found.

Valid moves are those to push a box from a reachable cell to an unblocked cell (not a wall or another box). If a move is to push a box into a dead corner, it's also considered invalid and thrown away in search tree.

