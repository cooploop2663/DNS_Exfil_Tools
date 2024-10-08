def calculate_length(subdomain, fulldomain):
    # Calculate lengths
    subdomain_length = len(subdomain)
    full_domain_length = len(subdomain) + len(fulldomain) + 1  # +1 for the dot separator

    # Check if the lengths are valid
    is_subdomain_valid = subdomain_length <= 63
    is_full_domain_valid = full_domain_length <= 253

    # Display results
    print(f"Subdomain length: {subdomain_length} characters ({'Valid' if is_subdomain_valid else 'Invalid'})")
    print(f"Full domain length: {full_domain_length} characters ({'Valid' if is_full_domain_valid else 'Invalid'})")

# Input subdomain and full domain
subdomain = input("Enter subdomain: ")
fulldomain = input("Enter full domain (e.g., example.com): ")

# Call the function
calculate_length(subdomain, fulldomain)
