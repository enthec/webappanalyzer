from pathlib import Path
import json

for file in Path("./src/technologies/").iterdir():
    print(file)
    with Path(file).open(encoding="utf-8") as f:
        content = json.loads(f.read())

    new_dict = dict()

    for techno, fields in content.items():
        if "requiresCategory" in fields and isinstance(fields["requiresCategory"], int):
            # print(fields["requiresCategory"])
            fields["requiresCategory"] = list([fields["requiresCategory"]])

        new_dict[techno] = fields

    with open(file, "w", encoding="utf-8") as f:
        json.dump(new_dict, f, indent=2, ensure_ascii=False)
