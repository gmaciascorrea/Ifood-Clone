import brazilcep

cep = "08030000"
address = brazilcep.get_address_from_cep(f'{cep}')

print(address)
    