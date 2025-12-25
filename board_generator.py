import random
from typing import List, Dict, Set, Tuple
import math

class CatanBoardGenerator:
    def __init__(self, expansion='base'):
        """
        Initialize the generator with terrain and number distributions
        
        Args:
            expansion: 'base', '5-6player', or 'custom'
        """
        self.expansion = expansion
        self.setup_distribution(expansion)
        
        # Define hex adjacency for standard Catan board (19 hexes)
        # Position indices 0-18
        self.adjacency = {
            0: [1, 3, 4],
            1: [0, 2, 4, 5],
            2: [1, 5, 6],
            3: [0, 4, 7, 8],
            4: [0, 1, 3, 5, 8, 9],
            5: [1, 2, 4, 6, 9, 10],
            6: [2, 5, 10, 11],
            7: [3, 8, 12],
            8: [3, 4, 7, 9, 12, 13],
            9: [4, 5, 8, 10, 13, 14],
            10: [5, 6, 9, 11, 14, 15],
            11: [6, 10, 15],
            12: [7, 8, 13, 16],
            13: [8, 9, 12, 14, 16, 17],
            14: [9, 10, 13, 15, 17, 18],
            15: [10, 11, 14, 18],
            16: [12, 13, 17],
            17: [13, 14, 16, 18],
            18: [14, 15, 17]
        }
    
    def setup_distribution(self, expansion):
        """Setup terrain and number distributions based on game type"""
        if expansion == 'base':
            self.terrains = [
                'Forest', 'Forest', 'Forest', 'Forest',
                'Pasture', 'Pasture', 'Pasture', 'Pasture',
                'Field', 'Field', 'Field', 'Field',
                'Hill', 'Hill', 'Hill',
                'Mountain', 'Mountain', 'Mountain',
                'Desert'
            ]
            self.numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        
        elif expansion == '5-6player':
            # 5-6 player extension adds more hexes
            self.terrains = [
                'Forest', 'Forest', 'Forest', 'Forest', 'Forest', 'Forest',
                'Pasture', 'Pasture', 'Pasture', 'Pasture', 'Pasture', 'Pasture',
                'Field', 'Field', 'Field', 'Field', 'Field', 'Field',
                'Hill', 'Hill', 'Hill', 'Hill', 'Hill',
                'Mountain', 'Mountain', 'Mountain', 'Mountain', 'Mountain',
                'Desert', 'Desert'
            ]
            self.numbers = [2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 
                          8, 8, 8, 9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12]
        
        elif expansion == 'custom':
            # Example custom distribution - modify as needed
            self.terrains = [
                'Forest', 'Forest', 'Forest',
                'Pasture', 'Pasture', 'Pasture',
                'Field', 'Field', 'Field',
                'Hill', 'Hill', 'Hill',
                'Mountain', 'Mountain', 'Mountain',
                'Gold', 'Gold', 'Gold',  # Custom terrain type
                'Desert'
            ]
            self.numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
    
    def generate_board(self, max_attempts=1000) -> List[Dict]:
        """
        Generate a balanced Catan board with constraints
        
        Args:
            max_attempts: Maximum number of attempts to generate a valid board
        """
        best_board = None
        best_score = float('inf')
        
        for attempt in range(max_attempts):
            board = self._generate_candidate_board()
            
            # Check hard constraints
            if not self._check_adjacent_high_numbers(board):
                continue
            
            if not self._check_desert_placement(board):
                continue
            
            # Score the board (lower is better)
            score = self._score_board(board)
            
            if score < best_score:
                best_score = score
                best_board = board
                
                # If we found a great board, use it
                if score < 50:  # Threshold for "good enough"
                    break
        
        return best_board if best_board else self._generate_candidate_board()
    
    def _generate_candidate_board(self) -> List[Dict]:
        """Generate a single candidate board"""
        shuffled_terrains = self.terrains.copy()
        random.shuffle(shuffled_terrains)
        
        shuffled_numbers = self.numbers.copy()
        random.shuffle(shuffled_numbers)
        
        board = []
        number_index = 0
        
        for i, terrain in enumerate(shuffled_terrains):
            hex_tile = {
                'position': i,
                'terrain': terrain,
                'number': None if terrain == 'Desert' else shuffled_numbers[number_index]
            }
            
            if terrain != 'Desert':
                number_index += 1
            
            board.append(hex_tile)
        
        return board
    
    def _check_adjacent_high_numbers(self, board: List[Dict]) -> bool:
        """Check that no 6s or 8s are adjacent"""
        high_value_positions = {
            h['position'] for h in board if h['number'] in [6, 8]
        }
        
        for pos in high_value_positions:
            adjacent_positions = self.adjacency.get(pos, [])
            if any(adj_pos in high_value_positions for adj_pos in adjacent_positions):
                return False
        
        return True
    
    def _check_desert_placement(self, board: List[Dict]) -> bool:
        """Check that desert is not on the edge of the board"""
        # Edge positions for standard 19-hex board
        edge_positions = {0, 1, 2, 3, 6, 7, 11, 12, 16, 17, 18}
        
        for hex_tile in board:
            if hex_tile['terrain'] == 'Desert' and hex_tile['position'] in edge_positions:
                return False
        
        return True
    
    def _score_board(self, board: List[Dict]) -> float:
        """
        Score a board based on balance criteria (lower is better)
        """
        score = 0.0
        
        # 1. Penalize clustering of same terrain types
        score += self._score_terrain_clustering(board) * 10
        
        # 2. Penalize unbalanced resource distribution
        score += self._score_resource_balance(board) * 5
        
        # 3. Penalize adjacent high pip count numbers
        score += self._score_pip_adjacency(board) * 3
        
        return score
    
    def _score_terrain_clustering(self, board: List[Dict]) -> float:
        """Score terrain clustering (higher = more clustered = worse)"""
        cluster_penalty = 0
        
        for pos, hex_tile in enumerate(board):
            if hex_tile['terrain'] == 'Desert':
                continue
            
            adjacent_positions = self.adjacency.get(pos, [])
            same_terrain_count = sum(
                1 for adj_pos in adjacent_positions
                if adj_pos < len(board) and board[adj_pos]['terrain'] == hex_tile['terrain']
            )
            
            # Penalize having 2+ adjacent hexes of same terrain
            if same_terrain_count >= 2:
                cluster_penalty += same_terrain_count
        
        return cluster_penalty
    
    def _score_resource_balance(self, board: List[Dict]) -> float:
        """Score resource distribution balance"""
        # Calculate total pip value per resource
        resource_pips = {}
        
        for hex_tile in board:
            terrain = hex_tile['terrain']
            if terrain != 'Desert':
                pip_count = self.get_pip_count(hex_tile['number'])
                resource_pips[terrain] = resource_pips.get(terrain, 0) + pip_count
        
        if not resource_pips:
            return 0
        
        # Calculate variance (lower variance = more balanced)
        avg_pips = sum(resource_pips.values()) / len(resource_pips)
        variance = sum((v - avg_pips) ** 2 for v in resource_pips.values()) / len(resource_pips)
        
        return math.sqrt(variance)
    
    def _score_pip_adjacency(self, board: List[Dict]) -> float:
        """Penalize adjacent hexes with high pip totals"""
        penalty = 0
        
        for pos, hex_tile in enumerate(board):
            if hex_tile['number'] is None:
                continue
            
            pip_count = self.get_pip_count(hex_tile['number'])
            if pip_count < 4:  # Only check high pip numbers
                continue
            
            adjacent_positions = self.adjacency.get(pos, [])
            for adj_pos in adjacent_positions:
                if adj_pos < len(board) and board[adj_pos]['number']:
                    adj_pip = self.get_pip_count(board[adj_pos]['number'])
                    if adj_pip >= 4:
                        penalty += 1
        
        return penalty / 2  # Divide by 2 since we count each pair twice
    
    def get_pip_count(self, number) -> int:
        """Get probability pips for a number"""
        if number is None:
            return 0
        pip_map = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
        return pip_map.get(number, 0)
    
    def display_board_visual(self, board: List[Dict]):
        """Display a visual hex grid representation"""
        print("\n" + "="*70)
        print("CATAN BOARD - VISUAL LAYOUT")
        print("="*70 + "\n")
        
        # Rows configuration for standard board: 3-4-5-4-3
        rows = [
            (board[0:3], 6),    # 3 hexes, offset 6
            (board[3:7], 3),    # 4 hexes, offset 3
            (board[7:12], 0),   # 5 hexes, offset 0
            (board[12:16], 3),  # 4 hexes, offset 3
            (board[16:19], 6)   # 3 hexes, offset 6
        ]
        
        for row_hexes, offset in rows:
            # Print hex tops
            print(" " * offset, end="")
            for _ in row_hexes:
                print("  ____    ", end="")
            print()
            
            # Print hex middle with terrain
            print(" " * offset, end="")
            for hex_tile in row_hexes:
                terrain_short = hex_tile['terrain'][:4].upper()
                print(f" /{terrain_short:4s}\\   ", end="")
            print()
            
            # Print hex middle with number
            print(" " * offset, end="")
            for hex_tile in row_hexes:
                number_str = str(hex_tile['number']) if hex_tile['number'] else "--"
                pips = self.get_pip_count(hex_tile['number'])
                print(f" | {number_str:2s}:{pips} |   ", end="")
            print()
            
            # Print hex bottoms
            print(" " * offset, end="")
            for _ in row_hexes:
                print(" \\____/   ", end="")
            print("\n")
    
    def display_board(self, board: List[Dict]):
        """Display the board in a readable format"""
        print("\n" + "="*70)
        print("CATAN BOARD LAYOUT - LIST VIEW")
        print("="*70)
        
        rows = [
            board[0:3], board[3:7], board[7:12], board[12:16], board[16:19]
        ]
        
        for row_num, row in enumerate(rows, 1):
            print(f"\nRow {row_num}:")
            for hex_tile in row:
                terrain = hex_tile['terrain']
                number = hex_tile['number'] if hex_tile['number'] else '--'
                pip_count = self.get_pip_count(hex_tile['number'])
                print(f"  Pos {hex_tile['position']:2d}: [{terrain:10s}] Number: {number:2} (Pips: {pip_count})")
        
        print("\n" + "="*70)
        self.display_statistics(board)
    
    def display_statistics(self, board: List[Dict]):
        """Display statistics about the board"""
        print("\nBoard Statistics:")
        
        # Terrain counts
        terrain_counts = {}
        for hex_tile in board:
            terrain = hex_tile['terrain']
            terrain_counts[terrain] = terrain_counts.get(terrain, 0) + 1
        
        print("\nTerrain Distribution:")
        for terrain, count in sorted(terrain_counts.items()):
            print(f"  {terrain}: {count}")
        
        # Resource pip distribution
        print("\nResource Pip Values (production probability):")
        resource_pips = {}
        for hex_tile in board:
            if hex_tile['terrain'] != 'Desert':
                terrain = hex_tile['terrain']
                pips = self.get_pip_count(hex_tile['number'])
                resource_pips[terrain] = resource_pips.get(terrain, 0) + pips
        
        for terrain, pips in sorted(resource_pips.items()):
            print(f"  {terrain}: {pips} pips")
        
        # High value hexes
        high_numbers = [h for h in board if h['number'] in [6, 8]]
        print(f"\nHigh-value hexes (6 & 8): {len(high_numbers)}")
        for hex_tile in high_numbers:
            print(f"  Position {hex_tile['position']:2d}: {hex_tile['terrain']} - {hex_tile['number']}")
        
        # Check adjacency
        violations = []
        for pos, hex_tile in enumerate(board):
            if hex_tile['number'] in [6, 8]:
                for adj_pos in self.adjacency.get(pos, []):
                    if adj_pos < len(board) and board[adj_pos]['number'] in [6, 8]:
                        violations.append((pos, adj_pos))
        
        if violations:
            print(f"\n⚠ WARNING: Adjacent 6/8s found: {violations}")
        else:
            print("\n✓ No adjacent 6s or 8s - Good!")
        
        # Check desert placement
        desert_positions = [h['position'] for h in board if h['terrain'] == 'Desert']
        edge_positions = {0, 1, 2, 3, 6, 7, 11, 12, 16, 17, 18}
        desert_on_edge = any(pos in edge_positions for pos in desert_positions)
        
        if desert_on_edge:
            print("⚠ WARNING: Desert is on the edge")
        else:
            print("✓ Desert is in interior positions - Good!")

def main():
    print("="*70)
    print("CATAN BOARD GENERATOR")
    print("="*70)
    
    # Choose expansion
    print("\nSelect game type:")
    print("1. Base game (3-4 players, 19 hexes)")
    print("2. 5-6 player extension (30 hexes)")
    print("3. Custom distribution")
    
    choice = input("\nEnter choice (1-3) [default: 1]: ").strip()
    
    expansion_map = {'1': 'base', '2': '5-6player', '3': 'custom', '': 'base'}
    expansion = expansion_map.get(choice, 'base')
    
    if expansion == '5-6player':
        print("\n⚠ Note: 5-6 player board uses different adjacency rules.")
        print("Visual display optimized for base game.")
    
    generator = CatanBoardGenerator(expansion=expansion)
    
    print(f"\nGenerating {expansion} board with balanced constraints...")
    print("(This may take a moment to find an optimal layout)\n")
    
    board = generator.generate_board()
    
    # Display options
    print("\nDisplay options:")
    print("1. Visual hex grid")
    print("2. List view")
    print("3. Both")
    
    display_choice = input("\nEnter choice (1-3) [default: 3]: ").strip() or '3'
    
    if display_choice in ['1', '3']:
        generator.display_board_visual(board)
    
    if display_choice in ['2', '3']:
        generator.display_board(board)
    
    # Option to generate another
    while True:
        choice = input("\nGenerate another board? (y/n): ").lower()
        if choice == 'y':
            board = generator.generate_board()
            if display_choice in ['1', '3']:
                generator.display_board_visual(board)
            if display_choice in ['2', '3']:
                generator.display_board(board)
        else:
            print("\nThanks for using the Catan Board Generator!")
            print("Perfect for your GitHub portfolio! 🎲")
            break

if __name__ == "__main__":
    main()