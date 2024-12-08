from django.shortcuts import render, redirect
from .models import Block

def root(request):
    blocks = Block.objects.all().order_by("-id").values()
    return render(request, "root.html", { "blocks": blocks })

def block(request, hash):
    block = Block.objects.get(hash=hash)
    transactions = block.transactions.split(";")
    transactions = map(lambda t: t.split(","), transactions)
    transactions_html = []
    for transaction in transactions:
        if transaction[0] == "MintTransaction":
            transactions_html.append(f"{transaction[1]} gets {transaction[2]} DD, ID: {transaction[3]}, Signature: {transaction[4]}")
        elif transaction[0] == "Transaction":
            transactions_html.append(f"{transaction[1]} sends {transaction[3]} DD to {transaction[2]}, ID: {transaction[4]}, Signature: {transaction[5]}")

    return render(request, "block.html", { "b": block, "transactions": transactions_html })

def reset(request):
    Block.objects.all().delete()
    return redirect("/")
