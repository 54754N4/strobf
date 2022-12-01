import Random
using Chain

struct PolymorphicEngine
    max_bits::Int
    min_ops::Int
    max_ops::Int
    MASK::Int
    MULTIPLICATIVE_LIMIT::Int
    ADDITIVE_LIMIT::Int

    PolymorphicEngine(max_bits, min_ops, max_ops) = 
        new(max_bits, min_ops, max_ops, (1 << max_bits) - 1, 1 << (max_bits // 2), )

    PolymorphicEngine() = new(5, 10, 16)
end


struct BitTransformation
    bits::Int
    mask::Int
    BitTransformation(bits) = new(rand(0:bits), (1 << bits) - 1)
end

overflow(val::Int, t:: BitTransformation) = val > ((1 << t.mask) - t.bits)

transform(bit::Int, t::BitTransformation) = bit+t.bits

inv_transform(bit::Int, t::BitTransformation) = bit-t.bits


function main()

    text = "Hello World!"
    bitarray = @chain text Vector{UInt8}(_) Vector{Int64}(_)
    println(text)
    println(bitarray)


    #engine = PolymorphicEngine()
    t = BitTransformation(666)

    cts = transform.(bitarray, Ref(t))
    println(cts)

    new_bitarray = inv_transform.(cts, Ref(t))
    println(new_bitarray)

    new_txt = @chain bitarray Char.(_) String println    

end

main()

