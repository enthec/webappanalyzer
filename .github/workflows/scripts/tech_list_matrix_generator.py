import os


def main():
    with open(os.environ["GITHUB_OUTPUT"], "w") as f:
        f.write(f"technologies={os.listdir('src/technologies')}\n")
    print(os.getenv("GITHUB_OUTPUT"))


if __name__ == '__main__':
    main()
