def sieve_of_eratosthenes(limit):
    primes = [True] * (limit + 1)
    primes[0] = primes[1] = False

    for i in range(2, int(limit**0.5) + 1):
        if primes[i]:
            for j in range(i * i, limit + 1, i):
                primes[j] = False

    prime_list = []
    for i in range(2, limit + 1):
        if primes[i]:
            prime_list.append(i)

    return prime_list

def main():
    n = 100
    prime_list = sieve_of_eratosthenes(n)
    
    if prime_list:
        print("Prime numbers up to", n, "are:", prime_list)
    else:
        print("No prime numbers found.")

if __name__ == "__main__":
    main()