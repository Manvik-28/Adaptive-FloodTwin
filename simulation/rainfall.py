def rainfall_to_runoff(rainfall_mm, runoff_coefficient=0.7):
    """
    Convert rainfall depth into effective runoff depth.

    rainfall_mm:
        Total rainfall in millimetres.

    runoff_coefficient:
        Fraction of rainfall becoming surface runoff.
    """

    runoff_mm = rainfall_mm * runoff_coefficient

    return runoff_mm


if __name__ == "__main__":

    for rainfall in [50, 100, 150, 200]:

        runoff = rainfall_to_runoff(rainfall)

        print(
            f"Rainfall: {rainfall} mm -> "
            f"Runoff: {runoff:.2f} mm"
        )