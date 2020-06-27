import random
import pyrtl
from pyrtl import *

#######################
### PROGRAM COUNTER ###
#######################

pc = pyrtl.Register(32, name='pc')

########################
# INSTRUCTION MEMBLOCK #
########################
i_mem = pyrtl.MemBlock(bitwidth=32,addrwidth=32,name='i_mem')
instr = pyrtl.WireVector(bitwidth=32, name='instr')
instr <<= i_mem[pc]

########################
## DECODE INSTRUCTION ##
########################

#Decodes R-type Instruction - DONE
def decode_instruction(instr):
   # output data
    op = pyrtl.WireVector(bitwidth=6, name='op')
    rs = pyrtl.WireVector(bitwidth=5, name='rs')
    rt = pyrtl.WireVector(bitwidth=5, name='rt')
    rd = pyrtl.WireVector(bitwidth=5, name='rd')
    sh = pyrtl.WireVector(bitwidth=5, name='sh')
    func = pyrtl.WireVector(bitwidth=6, name='func')
    imm = pyrtl.WireVector(bitwidth=16, name='imm')
    addr = pyrtl.WireVector(bitwidth=26, name='addr')

    #decode the instruction into its parts
    '''
    R-TYPE: op, rs, rt, rd, sh, funct
    I-TYPE: op, rs, rt, imm
    J-TYPE: op, addr
    '''
    op <<= instr[26:32] 
    rs <<= instr[21:26]
    rt <<= instr[16:21]
    rd <<= instr[11:16]
    sh <<= instr[6:11]
    func <<= instr[0:6]
    imm <<= instr[0:16]
    addr <<= instr[0:26] 
    return op, rs, rt, rd, sh, func, imm, addr

(op, rs, rt, rd, sh, func, imm, addr) = decode_instruction(instr)

#sign extend imm here: 
sign_ext_immed = imm.sign_extended(32)

#########################
##### CONTROL UNIT  #####
#########################

control_signals = pyrtl.WireVector(bitwidth=10, name='control_signals')
with pyrtl.conditional_assignment:
    #R-type
    with op==int('0', 16): 
        #ADD
        with func==int('20',16):
            control_signals |= int('280', 16)
        #AND
        with func==int('24',16):
            control_signals |= int('282',16)
        #SLT
        with func==int('2a',16):
            control_signals |= int('284',16)
    #ADDI
    with op==int('8',16):
        control_signals |= int('0a0', 16)
    #LUI
    with op==int('f',16):
        control_signals |= int('0a5', 16)
    #ORI
    with op==int('d',16):
        control_signals |= int('0c3',16)
    #LW
    with op==int('23',16):
        control_signals |= int('0a8',16)
    #SW
    with op==int('2b',16):
        control_signals |= int('030',16)
    #BEQ
    with op==int('4',16):
        control_signals |= int('301',16)

reg_dst = control_signals[9:10]
branch = control_signals[8:9]
reg_write = control_signals[7:8]
alu_src = control_signals[5:7]
mem_write = control_signals[4:5]
mem_to_reg = control_signals[3:4]
alu_op = control_signals[0:3]

#########################
## REGISTER FILE BLOCK ##
#########################

rf = pyrtl.MemBlock(bitwidth=32,addrwidth=32,name='rf',max_read_ports=3,asynchronous=True) 
r_data1 = pyrtl.WireVector(32,name='r_data1') #r_data1 is 32 bits long
r_data2 = pyrtl.WireVector(32,name='r_data2') #r_data2 is 32 bits long
w_reg = pyrtl.WireVector(32,name='w_reg')

#Below are the outputs of the reg memblock
#r_data1 <<= rf[rs] # r_data1 = value at register rs
#r_data2 <<= rf[rt] # r_data1 = value at register rt

with pyrtl.conditional_assignment:
    with rs == 0: 
        r_data1 |= int('0',16)
    with pyrtl.otherwise:
        r_data1 |= rf[rs]

with pyrtl.conditional_assignment:
    with rt == 0: 
        r_data2 |= int('0',16)
    with pyrtl.otherwise:
        r_data2 |= rf[rt]



#MUX FOR W_REG
with pyrtl.conditional_assignment:
    with reg_dst==int('0', 2): #ALU_in2 = rt  
        w_reg |= rt
    with reg_dst==int('1', 2): #ALU_in2 = immed
        w_reg |= rd

#MUX before ALU
alu_in2 = pyrtl.WireVector(32,name='alu_in2')
with pyrtl.conditional_assignment:
    with alu_src==int('0', 10): #ALU_in2 = value of rt
        alu_in2 |= r_data2 
    with alu_src==int('1', 10): #ALU_in2 = immed
        alu_in2 |= sign_ext_immed
    with alu_src==int('2',10):
        alu_in2 |= imm.zero_extended(32) #THIS IS FOR ORI

########################
## ALU IMPLEMENTATION ##
########################

alu_out = pyrtl.WireVector(bitwidth=32,name='alu_out')
zero_out = pyrtl.WireVector(bitwidth=1,name='zero_out')
with pyrtl.conditional_assignment:
    #ADD
    with alu_op==int('0',10):
        alu_out |= r_data1 + alu_in2
    #SUB
    with alu_op==int('1',10):
        alu_out |= r_data1 - alu_in2
    #AND
    with alu_op==int('2',10):
        alu_out |= r_data1 & alu_in2
    #OR
    with alu_op==int('3',10):
        alu_out |= r_data1 | alu_in2
    #SLT
    with alu_op==int('4',10):
        alu_out |= pyrtl.corecircuits.signed_lt(r_data1, alu_in2)
    #LUI
    with alu_op==int('5',10):
        alu_out |= pyrtl.corecircuits.shift_left_logical(alu_in2, pyrtl.Const(16))

with pyrtl.conditional_assignment:
    with alu_out==0:
        zero_out |= 1
    with pyrtl.otherwise:
        zero_out |= 0

##########################
## D_MEM MEMBLOCK BELOW ##
##########################

# D_MEM MEMBLOCK
d_mem = pyrtl.MemBlock(bitwidth=32,addrwidth=32,name='d_mem',asynchronous=True)
read_data = pyrtl.WireVector(32, name='read_data')
# LW - read_data has value at mem address alu_out
read_data <<= d_mem[alu_out] # read_data = value at memory address alu_out

#WRITE enable for D_MEM (writing onto memory)
# SW - STORE value of rt into memory address alu_out
d_mem[alu_out] <<= pyrtl.MemBlock.EnabledWrite(rf[rt], enable=mem_write)

#MUX AFTER D_MEM , SEL = MEM_TO_REG
#This will be the value that will be written into the register
w_data_val = pyrtl.WireVector(32,name='w_data_val')
with pyrtl.conditional_assignment:
    with mem_to_reg==int('0', 10): #ALU_in2 = rt  
        w_data_val |= alu_out
    with mem_to_reg==int('1', 10): #ALU_in2 = immed
        w_data_val |= read_data

#WRITE ENABLE FOR RF 
#pyrtl.helperfuncs.probe(w_data_val)
'''
with pyrtl.conditional_assignment:
    with w_reg!=0:
        rf[w_reg] |= pyrtl.MemBlock.EnabledWrite(w_data_val, enable=reg_write)
'''
rf[w_reg] <<= pyrtl.MemBlock.EnabledWrite(w_data_val, enable=reg_write)

######################
## ADDER FOR BRANCH ##
######################
next_instr = pyrtl.WireVector(32, name='next_instr')
sel = zero_out & branch #alu_out is the result of rs AND rt
#MUX for BRANCH
with pyrtl.conditional_assignment:
    with sel: # BRANCH
        next_instr |= sign_ext_immed + pc + 1
    with pyrtl.otherwise: # go to next instruction
        next_instr |= pc + 1
pc.next <<= next_instr

if __name__ == '__main__':
    """

    Here is how you can test your code.
    This is very similar to how the autograder will test your code too.

    1. Write a MIPS program. It can do anything as long as it tests the
       instructions you want to test.

    2. Assemble your MIPS program to convert it to machine code. Save
       this machine code to the "i_mem_init.txt" file.
       You do NOT want to use QtSPIM for this because QtSPIM sometimes
       assembles with errors. One assembler you can use is the following:

       https://alanhogan.com/asu/assembler.php

    3. Initialize your i_mem (instruction memory).

    4. Run your simulation for N cycles. Your program may run for an unknown
       number of cycles, so you may want to pick a large number for N so you
       can be sure that the program has "finished" its business logic.

    5. Test the values in the register file and memory to make sure they are
       what you expect them to be.

    6. (Optional) Debug. If your code didn't produce the values you thought
       they should, then you may want to call sim.render_trace() on a small
       number of cycles to see what's wrong. You can also inspect the memory
       and register file after every cycle if you wish.

    Some debugging tips:

        - Make sure your assembly program does what you think it does! You
          might want to run it in a simulator somewhere else (SPIM, etc)
          before debugging your PyRTL code.

        - Test incrementally. If your code doesn't work on the first try,
          test each instruction one at a time.

        - Make use of the render_trace() functionality. You can use this to
          print all named wires and registers, which is extremely helpful
          for knowing when values are wrong.

        - Test only a few cycles at a time. This way, you don't have a huge
          500 cycle trace to go through!

    """

    # Start a simulation trace
    sim_trace = pyrtl.SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}
    with open('test1.txt', 'r') as fin:
        i = 0
        for line in fin.readlines():
            i_mem_init[i] = int(line, 16)
            i += 1

    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        i_mem : i_mem_init
    })

    # Run for an arbitrarily large number of cycles.
    #CHANGE TO 500
    for cycle in range(500):
        sim.step({})

    # Use render_trace() to debug if your code doesn't work.
    #sim_trace.render_trace()
    #sim_trace.print_trace()

    #You can also print out the register file or memory like so if you want to debug:
    print(sim.inspect_mem(d_mem))
    print(sim.inspect_mem(rf))
    #print(sim.inspect(control_signals))
    #print(sim.inspect_mem(rf)[0])
    
    # Perform some sanity checks to see if your program worked correctly
    #assert (sim.inspect_mem(d_mem)[0] == 10)
    #assert(sim.inspect_mem(rf)[8] == 10)    # $v0 = rf[8]
    #assert(sim.inspect_mem(rf)[16] == 0x10000000)

    # Perform some sanity checks to see if your program worked correctly
    '''
    assert (sim.inspect_mem(rf)[16] == 65536)
    assert (sim.inspect_mem(rf)[17] == 1)
    assert (sim.inspect_mem(rf)[18] == 0)
    assert (sim.inspect_mem(rf)[19] == 5)
    assert (sim.inspect_mem(rf)[20] == 1)
    assert (sim.inspect_mem(rf)[21] == 65535)
    assert (sim.inspect_mem(d_mem)[0] == 10)
    assert (sim.inspect_mem(rf)[8] == 10)  # $v0 = rf[8]
    '''
    #test9.txt
    '''
    solution_rf = {2: 65535, 3: 4294901760, 4: 4294967295, 16: 0, 17: 65535, 18: 4294901760}
    assert(sim.inspect_mem(rf) == solution_rf)
    solution_d_mem = {}
    assert(sim.inspect_mem(d_mem) == solution_d_mem)
    print('Passed!')
    '''
    #i_mem_init2.txt
    '''
    solution_rf = {0: 4, 8: 2, 9: 2}
    assert(sim.inspect_mem(rf) == solution_rf)
    solution_d_mem = {}
    assert(sim.inspect_mem(d_mem) == solution_d_mem)
    '''

    
    solution_rf = {8: 0, 2: 4134731776, 16: 5}
    assert(sim.inspect_mem(rf) == solution_rf)
    solution_d_mem = {1: 4134731776}
    assert(sim.inspect_mem(d_mem) == solution_d_mem)
    print('Passed!')
    

    print('Passed!')



