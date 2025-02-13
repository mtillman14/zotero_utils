from pyalex import Works, Authors, Sources, Institutions, Concepts, Topics, Publishers, Funders

first_letter_types_dict = {
    "W": Works,
    "A": Authors,
    "S": Sources,
    "I": Institutions,
    "C": Concepts,
    "T": Topics,
    "P": Publishers,
    "F": Funders,
}

def get_entities_by_id(openalex_item_ids: list[str]) -> list:
    """
    Get entities from OpenAlex API by their IDs.

    Args:
        openalex_item_ids (list[str]): A list of item IDs.

    Returns:
        list: A list of entities.
    """

    # Check that the openalex_item_ids are not empty
    if not openalex_item_ids:
        raise ValueError("The list of item IDs is empty.")

    # Make sure that the item types are all the same
    first_letter = openalex_item_ids[0][0]
    for item_id in openalex_item_ids:
        if item_id[0] != first_letter:
            raise ValueError("All item IDs must be of the same type in this list.")


    # Can query the OpenAlex API for up to 50 entities at a time.
    entities = []
    for item_count in range(0, len(openalex_item_ids), 50):
        item_batch = openalex_item_ids[item_count:item_count + 50]
        entities.append(entities().get(openalex_item_ids=item_batch))
    return entities