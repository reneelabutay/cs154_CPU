# Testing that $zero is not changed throughout program execution

.text

main:
	add $t0, $zero, $zero # $zero is initially set to 0 so $t0 = 0.

	lui $v0 0xf673        # Loads large negative number into $v0
	sw $v0 0x1($zero)     # Stores the value from $v0 in d_mem[1]
	lw $zero 0x1($zero)   # this line shoudn't change $zero
	addi $s0, $zero, 0x5  # $s0 = 5
	addi $zero, $s0, 0x2  # This line also shoudn't change $zero

exit:
	beq $t0, $t0, exit



# Below is a test to ensure the program executed properly.
# Place these lines in the cpu.py file at the end of the simulation in __main__

# solution_rf = {8: 0, 2: 4134731776, 16: 5}
# assert(sim.inspect_mem(rf) == solution_rf)
# solution_d_mem = {1: 4134731776}
# assert(sim.inspect_mem(d_mem) == solution_d_mem)
# print('Passed!')
