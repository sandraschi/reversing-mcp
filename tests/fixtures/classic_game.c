/*
 * Classic Game Test Fixture - Early Windows Style Game
 *
 * This simulates a classic early Windows game like Nibbles/Ants
 * with text-based sprites, simple game loop, and basic algorithms.
 *
 * Features:
 * - Text-based graphics using ASCII characters
 * - Simple game state management
 * - Basic collision detection
 * - Score tracking
 * - Input handling simulation
 *
 * This represents the kind of code found in early Windows games
 * that would benefit from reverse engineering analysis.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Game constants - typical of early Windows games
#define BOARD_WIDTH 20
#define BOARD_HEIGHT 15
#define MAX_SNAKE_LENGTH 100
#define INITIAL_SNAKE_LENGTH 3

// ASCII sprites - common in early text-based games
#define SPRITE_HEAD '@'
#define SPRITE_BODY 'O'
#define SPRITE_FOOD '*'
#define SPRITE_WALL '#'
#define SPRITE_EMPTY ' '

// Game state structure
typedef struct {
    int x, y;  // Position
} Position;

typedef struct {
    Position body[MAX_SNAKE_LENGTH];
    int length;
    int direction;  // 0=up, 1=right, 2=down, 3=left
} Snake;

typedef struct {
    char board[BOARD_HEIGHT][BOARD_WIDTH];
    Snake snake;
    Position food;
    int score;
    int game_over;
} GameState;

// Function prototypes - typical game architecture
void initialize_game(GameState *game);
void update_game(GameState *game);
void render_board(const GameState *game);
int check_collision(const GameState *game, int x, int y);
void place_food(GameState *game);
void move_snake(GameState *game);
void handle_input(GameState *game, char input);

int main() {
    GameState game;
    char input;

    // Seed random number generator
    srand(time(NULL));

    printf("Classic Snake Game - Early Windows Style\n");
    printf("Use WASD to move, Q to quit\n\n");

    initialize_game(&game);

    // Main game loop - typical of early games
    while (!game.game_over) {
        render_board(&game);

        printf("Score: %d | Snake Length: %d\n", game.score, game.snake.length);
        printf("Input (WASD to move, Q to quit): ");
        scanf(" %c", &input);

        handle_input(&game, input);

        if (input == 'q' || input == 'Q') {
            game.game_over = 1;
        } else {
            update_game(&game);
        }
    }

    printf("\nGame Over! Final Score: %d\n", game.score);
    return 0;
}

void initialize_game(GameState *game) {
    int i, j;

    // Clear the board
    memset(game->board, SPRITE_EMPTY, sizeof(game->board));

    // Initialize snake
    game->snake.length = INITIAL_SNAKE_LENGTH;
    game->snake.direction = 1;  // Start moving right

    // Place snake in center-left
    for (i = 0; i < game->snake.length; i++) {
        game->snake.body[i].x = 5 + i;
        game->snake.body[i].y = BOARD_HEIGHT / 2;
    }

    // Initialize game state
    game->score = 0;
    game->game_over = 0;

    // Place initial food
    place_food(game);
}

void update_game(GameState *game) {
    int head_x, head_y;

    // Calculate new head position
    head_x = game->snake.body[0].x;
    head_y = game->snake.body[0].y;

    switch (game->snake.direction) {
        case 0: head_y--; break;  // Up
        case 1: head_x++; break;  // Right
        case 2: head_y++; break;  // Down
        case 3: head_x--; break;  // Left
    }

    // Check collisions
    if (check_collision(game, head_x, head_y)) {
        game->game_over = 1;
        return;
    }

    // Move snake body
    move_snake(game);

    // Update head position
    game->snake.body[0].x = head_x;
    game->snake.body[0].y = head_y;

    // Check if food eaten
    if (head_x == game->food.x && head_y == game->food.y) {
        game->snake.length++;
        game->score += 10;
        place_food(game);
    }
}

void move_snake(GameState *game) {
    int i;

    // Shift body segments
    for (i = game->snake.length - 1; i > 0; i--) {
        game->snake.body[i] = game->snake.body[i - 1];
    }
}

int check_collision(const GameState *game, int x, int y) {
    // Wall collision
    if (x < 0 || x >= BOARD_WIDTH || y < 0 || y >= BOARD_HEIGHT) {
        return 1;
    }

    // Self collision
    int i;
    for (i = 0; i < game->snake.length; i++) {
        if (game->snake.body[i].x == x && game->snake.body[i].y == y) {
            return 1;
        }
    }

    return 0;
}

void place_food(GameState *game) {
    do {
        game->food.x = rand() % BOARD_WIDTH;
        game->food.y = rand() % BOARD_HEIGHT;
    } while (check_collision(game, game->food.x, game->food.y));
}

void handle_input(GameState *game, char input) {
    switch (input) {
        case 'w': case 'W': game->snake.direction = 0; break;  // Up
        case 'd': case 'D': game->snake.direction = 1; break;  // Right
        case 's': case 'S': game->snake.direction = 2; break;  // Down
        case 'a': case 'A': game->snake.direction = 3; break;  // Left
    }
}

void render_board(const GameState *game) {
    int x, y, i;

    // Clear screen (simple version)
    printf("\n\n");

    // Top border
    for (x = 0; x < BOARD_WIDTH + 2; x++) {
        printf("%c", SPRITE_WALL);
    }
    printf("\n");

    // Game board
    for (y = 0; y < BOARD_HEIGHT; y++) {
        printf("%c", SPRITE_WALL);  // Left border

        for (x = 0; x < BOARD_WIDTH; x++) {
            char sprite = SPRITE_EMPTY;

            // Check if snake body segment here
            for (i = 0; i < game->snake.length; i++) {
                if (game->snake.body[i].x == x && game->snake.body[i].y == y) {
                    sprite = (i == 0) ? SPRITE_HEAD : SPRITE_BODY;
                    break;
                }
            }

            // Check if food here
            if (game->food.x == x && game->food.y == y) {
                sprite = SPRITE_FOOD;
            }

            printf("%c", sprite);
        }

        printf("%c\n", SPRITE_WALL);  // Right border
    }

    // Bottom border
    for (x = 0; x < BOARD_WIDTH + 2; x++) {
        printf("%c", SPRITE_WALL);
    }
    printf("\n");
}

/*
 * Additional functions that would be in a real game
 * but are here for reverse engineering analysis
 */

int calculate_score_multiplier(int length, int time_bonus) {
    // Score calculation algorithm - interesting for RE analysis
    return length * 10 + time_bonus * 2;
}

void save_high_score(int score, const char *player_name) {
    // Simple file I/O - common in games
    FILE *file = fopen("highscore.txt", "w");
    if (file) {
        fprintf(file, "%s:%d\n", player_name, score);
        fclose(file);
    }
}

int load_high_score() {
    // File reading - another common pattern
    FILE *file = fopen("highscore.txt", "r");
    int high_score = 0;

    if (file) {
        fscanf(file, "%*[^:]:%d", &high_score);
        fclose(file);
    }

    return high_score;
}