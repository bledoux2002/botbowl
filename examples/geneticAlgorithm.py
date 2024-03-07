## geneticAlgorithm.py, Genetic Algorithm Python implementation for use in Bot Bowl
## Benjamin Ledoux, created 03/04/2024 1:34 PM, last editted 03/04/2024 x:xx PM

import random
    
class GeneticAlgorithm:
    
    def __init__(self, chromoLen = 15, popSize = 100, mutRate = 0.01, keepCount = 0, targetVal = 1):
        self.CHROMO_LEN = chromoLen # Length of chromosome (num of genes)
        self.POP_SIZE = popSize # Size of population (num of chromosomes)
        self.MUT_RATE = mutRate # Rate of mutation (higher = more mutations)
        self.KEEP_COUNT = keepCount # Number of best fitted chromosomes to keep from population
        self.TARGET = targetVal # Target value (might be useless)

    # Create randomized starting population
    def initialize_pop(self):
        population = list()
        for _ in range(self.POP_SIZE):
            chromo = ""
            for _ in range(self.CHROMO_LEN):
                chromo += str(random.randint(0, 1))
            population.append(chromo)
        return population

    # Turn chromosome and fitness into tuple (currently pointless to be a whole function but might be changed later)
    def fitness_cal(self, chromo_from_pop, avgTDs):
        return [chromo_from_pop, avgTDs]

    # Return sorted list of best half of population based on fitness
    def selection(self, population):
        sorted_chromo_pop = sorted(population, key= lambda x: x[1]) # Sort by fitness
        return sorted_chromo_pop[:int(0.5*self.POP_SIZE)]

    # Creating new population using best half of old population
    def crossover(self, parents):
        offspring_cross = []
        for _ in range(self.POP_SIZE - self.KEEP_COUNT): # If keeping best of parents, only create enough to fill rest of population
            # Select random parents
            parent1 = random.choice(parents)
            parent2 = random.choice(parents)
            # random.choice(parents[:int(len(population) * 0.5)]) for use if not TOTALLY random

            # Extract chromosomes (offspring yet to be tested, no fitness values for them)
            p1 = parent1[0]
            p2 = parent2[0]

            crossover_point = random.randint(1, self.CHROMO_LEN-1) # Random split point for parents
            child =  p1[:crossover_point] + p2[crossover_point:]
            offspring_cross.extend([child])
        return offspring_cross

    # Apply mutations at random for *variety*
    def mutate(self, offspring):
        mutated_offspring = []
        for chromo in offspring:
            for i in range(self.CHROMO_LEN):
                if random.random() < self.MUT_RATE:
                    chromo[i] = str(random.randint(0, 1))
            mutated_offspring.append(chromo)
        return mutated_offspring

    # Combine best fitted from old population and offspring into new population
    def replace(self, bestFit, mutated):
        population = list()
        population.extend(bestFit[:self.KEEP_COUNT][0])
        population.extend(mutated)
        return population