# from decimal import Decimal
# import graphene
# from graphene_django import DjangoObjectType
# from django.db import transaction
# from django.core.exceptions import ValidationError, ObjectDoesNotExist
# from .models import Customer, Product, Order
# from datetime import datetime

# # ======================
# # GraphQL Types
# # ======================
# class CustomerType(DjangoObjectType):
#     class Meta:
#         model = Customer
#         fields = ("id", "name", "email", "phone")


# class ProductType(DjangoObjectType):
#     class Meta:
#         model = Product
#         fields = ("id", "name", "price", "stock")


# class OrderType(DjangoObjectType):
#     class Meta:
#         model = Order
#         fields = ("id", "customer", "products", "total_amount", "order_date")


# # ======================
# # Input Types
# # ======================
# class CustomerInput(graphene.InputObjectType):
#     name = graphene.String(required=True)
#     email = graphene.String(required=True)
#     phone = graphene.String()


# class ProductInput(graphene.InputObjectType):
#     name = graphene.String(required=True)
#     price = graphene.Float(required=True)
#     stock = graphene.Int()


# class OrderInput(graphene.InputObjectType):
#     customer_id = graphene.ID(required=True)
#     product_ids = graphene.List(graphene.ID, required=True)
#     order_date = graphene.DateTime()


# # ======================
# # Mutations
# # ======================
# class CreateCustomer(graphene.Mutation):
#     class Arguments:
#         input = CustomerInput(required=True)

#     customer = graphene.Field(CustomerType)
#     message = graphene.String()

#     def mutate(self, info, input):
#         if Customer.objects.filter(email=input.email).exists():
#             raise Exception("Email already exists")
#         try:
#             customer = Customer(
#                 name=input.name,
#                 email=input.email,
#                 phone=input.phone
#             )
#             customer.full_clean()
#             customer.save()
#             return CreateCustomer(customer=customer, message="Customer created successfully")
#         except ValidationError as e:
#             raise Exception(f"Validation error: {e}")



# class BulkCreateCustomers(graphene.Mutation):
#     class Arguments:
#         input = graphene.List(CustomerInput, required=True)

#     customers = graphene.List(CustomerType)
#     errors = graphene.List(graphene.String)

#     def mutate(self, info, input):
#         created_customers = []
#         errors = []

#         for cust in input:
#             try:
#                 # Check duplicate email
#                 if Customer.objects.filter(email=cust.email).exists():
#                     errors.append(f"Email already exists: {cust.email}")
#                     continue

#                 customer = Customer(name=cust.name, email=cust.email, phone=cust.phone)
#                 customer.full_clean()  # Validates phone/email formats
#                 customer.save()
#                 created_customers.append(customer)

#             except ValidationError as e:
#                 # Capture specific field errors
#                 field_errors = []
#                 for field, messages in e.message_dict.items():
#                     for msg in messages:
#                         field_errors.append(f"{field}: {msg}")
#                 errors.append(f"{cust.email or cust.name} - Validation failed: {', '.join(field_errors)}")

#             except Exception as e:
#                 errors.append(f"{cust.email or cust.name} - {str(e)}")

#         return BulkCreateCustomers(customers=created_customers, errors=errors)


# class CreateProduct(graphene.Mutation):
#     class Arguments:
#         input = ProductInput(required=True)

#     product = graphene.Field(ProductType)

#     def mutate(self, info, input):
#         # Convert to Decimal to avoid type issues
#         from decimal import Decimal
#         price = Decimal(str(input.price)) 
#         # try:
#         #     price = Decimal(str(input.price))
#         # except:
#         #     raise Exception("Invalid price format")

#         if price <= 0:
#             raise Exception("Price must be positive")
#         if input.stock is not None and input.stock < 0:
#             raise Exception("Stock cannot be negative")

#         product = Product(name=input.name, price=price, stock=input.stock or 0)
#         product.save()
#         return CreateProduct(product=product)


# class CreateOrder(graphene.Mutation):
#     class Arguments:
#         input = OrderInput(required=True)

#     order = graphene.Field(OrderType)

#     def mutate(self, info, input):
#         try:
#             customer = Customer.objects.get(pk=input.customer_id)
#         except ObjectDoesNotExist:
#             raise Exception("Invalid customer ID")

#         products = Product.objects.filter(pk__in=input.product_ids)
#         if not products.exists():
#             raise Exception("Invalid product IDs")
#         if products.count() != len(input.product_ids):
#             raise Exception("Some product IDs are invalid")

#         # total_amount = sum([float(p.price) for p in products])
#         total_amount = sum((p.price for p in products), Decimal("0.00"))

#         order = Order(
#             customer=customer,
#             total_amount=total_amount,
#             order_date=input.order_date or datetime.now()
#         )
#         order.save()
#         order.products.set(products)

#         return CreateOrder(order=order)


# # ======================
# # Root Query & Mutation
# # ======================
# class Query(graphene.ObjectType):
#     customers = graphene.List(CustomerType)
#     products = graphene.List(ProductType)
#     orders = graphene.List(OrderType)

#     def resolve_customers(root, info):
#         return Customer.objects.all()

#     def resolve_products(root, info):
#         return Product.objects.all()

#     def resolve_orders(root, info):
#         return Order.objects.all()


# class Mutation(graphene.ObjectType):
#     create_customer = CreateCustomer.Field()
#     bulk_create_customers = BulkCreateCustomers.Field()
#     create_product = CreateProduct.Field()
#     create_order = CreateOrder.Field()

import re
import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from decimal import Decimal
from django.utils import timezone

from crm.filters import CustomerFilter, OrderFilter, ProductFilter
from graphene_django.filter import DjangoFilterConnectionField

from .models import Customer, Product, Order
from django.db.models import Q
from .models import Product
from graphene_django.types import DjangoObjectType


# =====================
# GraphQL Types
# =====================
# class CustomerType(DjangoObjectType):
#     class Meta:
#         model = Customer
#         fields = "__all__"
#         filterset_class = CustomerFilter
#         interfaces = (graphene.relay.Node,)

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "created_at")
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'created_at': ['gte', 'lte'],
        }
        interfaces = (graphene.relay.Node,)  # Needed for connections

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)


# =====================
# Input Types
# =====================
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)  # accept float from client
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# =====================
# Mutations
# =====================
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []

        # Validate unique email
        if Customer.objects.filter(email=input.email).exists():
            errors.append("Email already exists.")

        # Validate phone format if provided
        if input.phone:
            phone_pattern = r"^(\+\d{10,15}|\d{3}-\d{3}-\d{4}|\d{10})$"
            if not re.match(phone_pattern, input.phone):
                errors.append("Invalid phone number format.")
                if errors:
                 return CreateCustomer(customer=None, message="Failed to create customer", errors=errors)

        customer = Customer(
            name=input.name,
            email=input.email,
            phone=input.phone or ""
        )
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully", errors=[])


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created_customers = []
        errors = []

        for idx, cust in enumerate(input, start=1):
            if Customer.objects.filter(email=cust.email).exists():
                errors.append(f"[Row {idx}] Email '{cust.email}' already exists.")
                continue
            # if cust.phone:
            #     phone_pattern = r"^(\+\d{10,15}|\d{3}-\d{3}-\d{4}|\d{10})$"
            #     if not re.match(phone_pattern, cust.phone):
            #         errors.append(f"[Row {idx}] Invalid phone format for '{cust.name}'.")
            #         continue
            customer = Customer(name=cust.name, email=cust.email, phone=cust.phone or "")
            customer.save()
            created_customers.append(customer)

        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []

        # Validation
        if input.price <= 0:
            errors.append("Price must be positive.")
        if input.stock is not None and input.stock < 0:
            errors.append("Stock cannot be negative.")

        if errors:
            return CreateProduct(product=None, errors=errors)

        # Convert float to Decimal safely
        price = Decimal(str(input.price))

        product = Product(
            name=input.name,
            price=price,
            stock=input.stock or 0
        )
        product.save()
        return CreateProduct(product=product, errors=[])


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []

        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except ObjectDoesNotExist:
            errors.append("Invalid customer ID.")
            return CreateOrder(order=None, errors=errors)

        products = Product.objects.filter(pk__in=input.product_ids)
        if not products.exists():
            errors.append("Invalid product IDs.")
        if products.count() != len(input.product_ids):
            errors.append("Some product IDs are invalid.")

        if errors:
            return CreateOrder(order=None, errors=errors)

        # Sum prices as Decimal
        total_amount = sum((p.price for p in products), Decimal("0.00"))

        order = Order(
            customer=customer,
            total_amount=total_amount,
            order_date=input.order_date or timezone.now()
        )
        order.save()
        order.products.set(products)

        return CreateOrder(order=order, errors=[])


# =====================
# Query & Mutation Registration
# =====================

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    
    all_customers = DjangoFilterConnectionField(
        CustomerType, 
        order_by=graphene.List(of_type=graphene.String),filter=graphene.String(),
        search=graphene.String()
    )
    
       
    all_products = DjangoFilterConnectionField(
        ProductType, 
        order_by=graphene.List(of_type=graphene.String),filter=graphene.String(),
        search=graphene.String()
    )
    all_orders = DjangoFilterConnectionField(
        OrderType, 
        order_by=graphene.List(of_type=graphene.String),filter=graphene.String(),
        search=graphene.String()
    )

    def resolve_all_customers(self, info, order_by=None, search=None, **kwargs):
        qs = Customer.objects.all()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_products(self, info, order_by=None, filter=None, search=None, **kwargs):
        qs = Product.objects.all()

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        if filter:
            # If filter is a JSON string, parse it
            try:
                import json
                filter_data = json.loads(filter)
                if "priceGte" in filter_data:
                    qs = qs.filter(price__gte=filter_data["priceGte"])
                if "priceLte" in filter_data:
                    qs = qs.filter(price__lte=filter_data["priceLte"])
            except json.JSONDecodeError:
                pass  # handle invalid filter format

        if order_by:
            qs = qs.order_by(*order_by)

        return qs


    def resolve_all_orders(self, info, order_by=None, search=None, **kwargs):
        qs = Order.objects.all()
        if search:
            qs = qs.filter(
                Q(order_number__icontains=search) |
                Q(customer__name__icontains=search)
            )
        if order_by:
            qs = qs.order_by(*order_by)
        return qs
# class Query(graphene.ObjectType):
#     hello = graphene.String(default_value="Hello, GraphQL!")
    
#     all_customers = DjangoFilterConnectionField(CustomerFilter, order_by=graphene.List(of_type=graphene.String))
#     all_products = DjangoFilterConnectionField(ProductFilter, order_by=graphene.List(of_type=graphene.String))
#     all_orders = DjangoFilterConnectionField(OrderFilter, order_by=graphene.List(of_type=graphene.String))

#     def resolve_all_customers(self, info, order_by=None, **kwargs):
#         qs = Customer.objects.all()
#         if order_by:
#             qs = qs.order_by(*order_by)
#         return qs

#     def resolve_all_products(self, info, order_by=None, **kwargs):
#         qs = Product.objects.all()
#         if order_by:
#             qs = qs.order_by(*order_by)
#         return qs

#     def resolve_all_orders(self, info, order_by=None, **kwargs):
#         qs = Order.objects.all()
#         if order_by:
#             qs = qs.order_by(*order_by)
#         return qs
# class Query(graphene.ObjectType):
#     hello = graphene.String(default_value="Hello, GraphQL!")
#     customers = graphene.List(CustomerType)
#     products = graphene.List(ProductType)
#     orders = graphene.List(OrderType)

#     def resolve_customers(root, info):
#         return Customer.objects.all()

#     def resolve_products(root, info):
#         return Product.objects.all()

#     def resolve_orders(root, info):
#         return Order.objects.all()


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()



class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "stock")

class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        pass  # no arguments needed

    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(ProductType)

    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated_products = []
        for product in low_stock_products:
            product.stock += 10  # simulate restock
            product.save()
            updated_products.append(product)

        return UpdateLowStockProducts(
            success=True,
            message=f"{len(updated_products)} products updated at {timezone.now()}",
            updated_products=updated_products
        )

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()
