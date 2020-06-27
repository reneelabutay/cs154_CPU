.text

main:
    lui $s0, 0x1
    and $t0 $t0 $zero # to = 0
    slt $s1, $t0, $s0
    slt  $s2, $s0, $t0
    ori $s3, $zero, 0x5
    and $s4, $s3, $s1
    ori $s5, $zero, 0xFFFF
    and $t1, $t1, $zero # t1 = 0
    addi $t1, $t1, 0x000A # t1 = 10
loop:
    beq $t0, $t1, exit # branch to lw v0 0 zero if equal
    
    # just these 5 lines
    # and $t2, $t2, $zero # t2 = 0
    addi $t2, $t2, 0x4
    lw $t3, 0x0000($t2) # load datamem[0] into t3 
    addi $t3, $t3, 0x0001 # t3 = t3+1
    sw $t3, 0x0000($t2) # store t3 at data_mem[t2]
    addi $t0, $t0, 0x0001 # t0 += 1
    
    
    beq $zero, $zero, loop # branch back to beq t0, t1, 6
exit:
    lw $v0, 0x0000($zero) # v0 = 0
    beq $v0, $v0, 0xFFFE # branch back to this instruction forever