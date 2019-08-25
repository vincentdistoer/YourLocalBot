def owners(ctx):
    x = [421698654189912064, 291933031919255552,
                                 414746664507801610,
                                 493790026115579905, 344878404991975427]
    users =[]
    for user in x:
        users.append(ctx.bot.get_user(x))
    return users
