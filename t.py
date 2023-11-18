import random

def guess_number_game():
    number_to_guess = 98
    attempts = 0

    for guess in range(1, 101):  # Simulating guesses from 1 to 100
        attempts += 1
        if guess == number_to_guess:
            break

        if attempts >= 10:  # Limit to 10 attempts for demonstration
            print(f"Game over. The number was {number_to_guess}.")
            break

guess_number_game()