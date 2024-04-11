## geneticAlgorithm.py, Genetic Algorithm Python implementation for use in Bot Bowl
## Benjamin Ledoux, created 03/04/2024 1:34 PM, last editted 03/04/2024 x:xx PM

import random

class GeneticAlgorithm:

    def __init__(self, chromoLen = 79, popSize = 100, mutRate = 0.01, keepCount = 0, targetVal = 1):
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
            for _ in range(70): # Genes 1-70
                chromo += str(random.randint(0, 1))
            for _ in range(2): # Genes 71-78
                tempVal = 3
                while tempVal == 3: # Make sure gene is equal from 0 to 2, not 3
                    tempGene = ""
                    for i in range(2):
                        tempGene += str(random.randint(0, 1))
                    tempVal = int(tempGene, 2)
                prevVal = tempVal
                chromo += tempGene
                while tempVal == 3 or tempVal == prevVal: # Make sure gene is equal from 0 to 2, not 3
                    tempGene = ""
                    for i in range(2):
                        tempGene += str(random.randint(0, 1))
                    tempVal = int(tempGene, 2)
                chromo += tempGene
            chromo += str(random.randint(0, 1)) # Gene 79
            population.append(chromo)
        return population

    # Turn chromosome and fitness into tuple (currently pointless to be a whole function but might be changed later)
    def fitness_cal(self, chromo_from_pop, ballProg, tdsFor, tdsAgainst):
        fit = (ballProg * 0.1) + tdsFor - tdsAgainst
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
    def selection(self, population, pressure):
        # Choose k individuals from entire pop
        # Choose best individual
        selected = []
        for _ in range(self.POP_SIZE):
            tournament = []
            for _ in range(pressure):
                index = random.randint(0, self.POP_SIZE - 1)
                tournament.append(population[index])
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
