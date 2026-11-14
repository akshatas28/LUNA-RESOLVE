import rasterio

path = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

with rasterio.open(path) as src:
    print("RASTER TAGS")
    print("=" * 60)

    for key, value in src.tags().items():
        print(f"{key}: {value}")

    print("\nNAMESPACED TAGS")
    print("=" * 60)

    for namespace in src.tag_namespaces():
        print(f"\nNamespace: {namespace}")

        for key, value in src.tags(ns=namespace).items():
            print(f"{key}: {value}")

    print("\nSUBDATASETS")
    print("=" * 60)

    print(src.subdatasets)