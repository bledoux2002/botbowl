## geneticAlgorithm.py, Genetic Algorithm Python implementation for use in Bot Bowl
## Benjamin Ledoux, created 03/04/2024 1:34 PM, last editted 03/04/2024 x:xx PM

import random
import math

class GeneticAlgorithm:

    def __init__(self, chromoLen = 134, popSize = 100, mutRate = 0.01, keepCount = 0):
        self.CHROMO_LEN = chromoLen # Length of chromosome (num of genes)
        self.POP_SIZE = popSize # Size of population (num of chromosomes)
        self.MUT_RATE = mutRate # Rate of mutation (higher = more mutations)
        self.KEEP_COUNT = keepCount # Number of best fitted chromosomes to keep from population

    # Create randomized starting population
    def initialize_pop(self):
        population = list()
        for _ in range(self.POP_SIZE):
            chromo = ""
            for _ in range(134): # Genes 1-134
                chromo += str(random.randint(0, 1))
            population.append(chromo)
        return population

    # Turn chromosome and fitness into tuple (currently pointless to be a whole function but might be changed later)
    def fitness_cal(self, chromo_from_pop, ballProg, tdsFor, tdsAgainst, wins, losses, games):
        fit = (ballProg * 0.01) + (0.1 * (tdsFor - tdsAgainst)) + (3 * wins) + (games - (wins + losses))
        return [chromo_from_pop, fit]

    # Return sorted list of best half of population based on fitness
    """
	REPLACED WITH TOURNAMENT STYLE SELECTION
	RETURNS TWO PARENTS FOR CROSSOVER, WILL BE CALLED ENOUGH TIMES TO FILL POPULATIONS
	maybe pull some of that code into here to clean up gaScriptedBot.py?
	roulette sounds better to me
    def selection(self, population):
        sorted_chromo_pop = sorted(population, key= lambda x: x[1], reverse=True) # Sort by fitness
        return sorted_chromo_pop[:int(0.1*self.POP_SIZE)]
    """
    
    # Tournament Style selection
    def selection(self, population, pressurePercentage):
        # Choose k individuals from entire pop
        # Choose best individual
        selected = []
        pressure = math.ceil(self.POP_SIZE * (pressurePercentage / 100))
        for _ in range(self.POP_SIZE):
            tournament = []
            temp_pop = population.copy()
            for i in range(pressure):
                if i < pressure - 1:
                    index = random.randint(0, len(temp_pop) - 1)
                else:
                    index = 0
                tournament.append(temp_pop.pop(index))
            tournament_sorted = sorted(tournament, key= lambda x: x[1], reverse=True)
            selected.append(tournament_sorted[0])
        return selected

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
            offspring_cross.append(child)
        return offspring_cross

    # Apply mutations at random for *variety*
    def mutate(self, offspring):
        mutated_offspring = []
        for chromo in offspring:
            new_chromo = ""
            for i in range(self.CHROMO_LEN):
                if random.random() < self.MUT_RATE:
                    if chromo[i] == "0":
                        new_chromo += "1"
                    elif chromo[i] == "1":
                        new_chromo += "0"
                    else:
#                        print("Issue mutating chromosome, using random instead")
                        new_chromo += str(random.randint(0, 1))
                else:
                    new_chromo += chromo[i]
            mutated_offspring.append(new_chromo)
        return mutated_offspring

    # Combine best fitted from old population and offspring into new population
    def replace(self, bestFit, mutated):
        population = list()
        if self.KEEP_COUNT > 0:
#            print(f"Chromosomes to keep: {bestFit[:self.KEEP_COUNT[0]]}. Fitnesses: {bestFit[:self.KEEP_COUNT[1]]}")
            for i in range (self.KEEP_COUNT):
                population.append(bestFit[i][0])
        population.extend(mutated)
        return population
