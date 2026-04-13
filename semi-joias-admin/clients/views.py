# View: Exibir clientes
    #/ Filtrar clientes por nome e celular


from django.shortcuts import render, redirect, get_object_or_404

from .models import Cliente

def exibir_clientes(request):
    nome = request.GET.get('nome', '').strip()
    celular = request.GET.get('celular', '').strip()
    
    clientes = Cliente.objects.param_filter(
        nome=nome,
        celular=celular
    )
        
    return render(request, 'clients/clientes.html', {
        'clientes': clientes,
        'active': 'clientes',
        'name_filter': nome,
        'phone_filter': celular,
        })

def cadastrar_cliente(request):
    if request.method == "GET":
        return render(request, 'clients/criar_cliente.html')
    
    elif request.method == "POST":
        name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone_number')
        
        client = Cliente(
            first_name=name,
            last_name=last_name,
            phone_number=phone,
        )
        client.save()
        return redirect('clients:lista')

def atualizar_cliente(request, id):
    client = get_object_or_404(Cliente, id=id)
    
    if request.method == "GET":
        return render(request, 'clients/atualizar_cliente.html', {'cliente': client})
    
    elif request.method == "POST":
        client.first_name = request.POST.get('first_name')
        client.last_name = request.POST.get('last_name')
        client.phone_number = request.POST.get('phone_number')

        client.save()
        return redirect('clients:lista')
    
def deletar_cliente(request, id):
    client = get_object_or_404(Cliente, id=id)
    client.delete()
    return redirect('clients:lista')