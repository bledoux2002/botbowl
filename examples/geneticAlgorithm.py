## geneticAlgorithm.py, Genetic Algorithm Python implementation for use in Bot Bowl
## Benjamin Ledoux, created 03/04/2024 1:34 PM, last editted 03/04/2024 x:xx PM

import random
    
class GeneticAlgorithm:
    
    def __init__(self, chromoLen = 15, popSize = 10, mutRate = 0.1, targetVal = 1):
        self.CHROMO_LEN = chromoLen
        self.POP_SIZE = popSize
        self.MUT_RATE = mutRate
        self.TARGET = targetVal

    def initialize_pop(self):
        population = list()

        for _ in range(self.POP_SIZE):
            population.append(str(random.getrandbits(self.CHROMO_LEN)))

        return population

    def crossover(self, population):
        offspring_cross = []
        for _ in range(int(len(population))): # Half size of pop to be added to best half of old pop
            parent1 = random.choice(population[int(len(population) * 0.5):])
            parent2 = random.choice(population[:int(len(population) * 0.5)])

            # Only need chromosomes, not fitness value
            p1 = parent1[0]
            p2 = parent2[0]

            crossover_point = random.randint(1, self.CHROMO_LEN-1) ## Random split point for parents
            child =  p1[:crossover_point] + p2[crossover_point:]
            offspring_cross.extend([child])
        return offspring_cross

    def mutate(self, offspring):
        mutated_offspring = []

        for chromo in offspring:
            for i in range(self.CHROMO_LEN):
                if random.random() < self.MUT_RATE:
                    chromo[i] = str(random.getrandbits(1))
            mutated_offspring.append(chromo)
        return mutated_offspring

    def selection(self, population):
        sorted_chromo_pop = sorted(population, key= lambda x: x[1]) # Sort by fitness
        return sorted_chromo_pop[:int(0.5*self.POP_SIZE)]

    def fitness_cal(self, chromo_from_pop, avgTDs):
        return [chromo_from_pop, avgTDs]

    def replace(self, population_eval, mutated):
        population = list()
        population.extend(population_eval[:][0])
        population.extend(mutated)
        return population

def main(MUT_RATE = 0.1, TARGET = 1):
    ga = GeneticAlgorithm()
    # 1) initialize population
    initial_population = ga.initialize_pop(TARGET)
    found = False
    population = []
    generation = 1

    # 2) Calculating the fitness for the current population
    for _ in range(len(initial_population)):
        population.append(ga.fitness_cal(TARGET, initial_population[_]))

    # now population has 2 things, [chromosome, fitness]
    # 3) now we loop until TARGET is found
    while not found:

        # 3.1) select best people from current population
        selected = ga.selection(population, TARGET)

        # 3.2) mate parents to make new generation
        population = sorted(population, key= lambda x:x[1])
        crossovered = ga.crossover(selected, len(TARGET), population)

        # 3.3) mutating the childeren to diversfy the new generation
        mutated = ga.mutate(crossovered, MUT_RATE)

        new_gen = []
        for _ in mutated:
            new_gen.append(ga.fitness_cal(TARGET, _))

        # 3.4) replacement of bad population with new generation
        # we sort here first to compare the least fit population with the most fit new_gen

        population = ga.replace(new_gen, population)

        
        if (population[0][1] == 0):
            print('Target found')
            print('String: ' + str(population[0][0]) + ' Generation: ' + str(generation) + ' Fitness: ' + str(population[0][1]))
            break
        print('String: ' + str(population[0][0]) + ' Generation: ' + str(generation) + ' Fitness: ' + str(population[0][1]))
        generation+=1

if __name__ == "__main__":
    main()