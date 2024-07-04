import { getParserRegexes } from './regex.js';
import { trimNewLines, appendLine, getCommentFilter, gpgFilter, truncateToScissor } from './utils.js';
import { defaultOptions } from './options.js';
/**
 * Helper to create commit object.
 * @param initialData - Initial commit data.
 * @returns Commit object with empty data.
 */
export function createCommitObject(initialData = {}) {
    // @ts-expect-error: You can read properties from `Commit` without problems, but you can't assign object to this type. So here is helper for that.
    return {
        merge: null,
        revert: null,
        header: null,
        body: null,
        footer: null,
        notes: [],
        mentions: [],
        references: [],
        ...initialData
    };
}
/**
 * Commit message parser.
 */
export class CommitParser {
    options;
    regexes;
    lines = [];
    lineIndex = 0;
    commit = createCommitObject();
    constructor(options = {}) {
        this.options = {
            ...defaultOptions,
            ...options
        };
        this.regexes = getParserRegexes(this.options);
    }
    currentLine() {
        return this.lines[this.lineIndex];
    }
    nextLine() {
        return this.lines[this.lineIndex++];
    }
    isLineAvailable() {
        return this.lineIndex < this.lines.length;
    }
    parseReference(input, action) {
        const { regexes } = this;
        const matches = regexes.referenceParts.exec(input);
        if (!matches) {
            return null;
        }
        let [raw, repository = null, prefix, issue] = matches;
        let owner = null;
        if (repository) {
            const slashIndex = repository.indexOf('/');
            if (slashIndex !== -1) {
                owner = repository.slice(0, slashIndex);
                repository = repository.slice(slashIndex + 1);
            }
        }
        return {
            raw,
            action,
            owner,
            repository,
            prefix,
            issue
        };
    }
    parseReferences(input) {
        const { regexes } = this;
        const regex = input.match(regexes.references)
            ? regexes.references
            : /()(.+)/gi;
        const references = [];
        let matches;
        let action;
        let sentence;
        let reference;
        while (true) {
            matches = regex.exec(input);
            if (!matches) {
                break;
            }
            action = matches[1] || null;
            sentence = matches[2] || '';
            while (true) {
                reference = this.parseReference(sentence, action);
                if (!reference) {
                    break;
                }
                references.push(reference);
            }
        }
        return references;
    }
    skipEmptyLines() {
        let line = this.currentLine();
        while (line !== undefined && !line.trim()) {
            this.nextLine();
            line = this.currentLine();
        }
    }
    parseMerge() {
        const { commit, options } = this;
        const correspondence = options.mergeCorrespondence || [];
        const merge = this.currentLine();
        const matches = merge && options.mergePattern
            ? merge.match(options.mergePattern)
            : null;
        if (matches) {
            this.nextLine();
            commit.merge = matches[0] || null;
            correspondence.forEach((key, index) => {
                commit[key] = matches[index + 1] || null;
            });
            return true;
        }
        return false;
    }
    parseHeader(isMergeCommit) {
        if (isMergeCommit) {
            this.skipEmptyLines();
        }
        const { commit, options } = this;
        const correspondence = options.headerCorrespondence || [];
        const header = this.nextLine();
        let matches = null;
        if (header) {
            if (options.breakingHeaderPattern) {
                matches = header.match(options.breakingHeaderPattern);
            }
            if (!matches && options.headerPattern) {
                matches = header.match(options.headerPattern);
            }
        }
        if (header) {
            commit.header = header;
        }
        if (matches) {
            correspondence.forEach((key, index) => {
                commit[key] = matches[index + 1] || null;
            });
        }
    }
    parseMeta() {
        const { options, commit } = this;
        if (!options.fieldPattern || !this.isLineAvailable()) {
            return false;
        }
        let matches;
        let field = null;
        let parsed = false;
        while (this.isLineAvailable()) {
            matches = this.currentLine().match(options.fieldPattern);
            if (matches) {
                field = matches[1] || null;
                this.nextLine();
                continue;
            }
            if (field) {
                parsed = true;
                commit[field] = appendLine(commit[field], this.currentLine());
                this.nextLine();
            }
            else {
                break;
            }
        }
        return parsed;
    }
    parseNotes() {
        const { regexes, commit } = this;
        if (!this.isLineAvailable()) {
            return false;
        }
        const matches = this.currentLine().match(regexes.notes);
        let references = [];
        if (matches) {
            const note = {
                title: matches[1],
                text: matches[2]
            };
            commit.notes.push(note);
            commit.footer = appendLine(commit.footer, this.currentLine());
            this.nextLine();
            while (this.isLineAvailable()) {
                if (this.parseMeta()) {
                    return true;
                }
                if (this.parseNotes()) {
                    return true;
                }
                references = this.parseReferences(this.currentLine());
                if (references.length) {
                    commit.references.push(...references);
                }
                else {
                    note.text = appendLine(note.text, this.currentLine());
                }
                commit.footer = appendLine(commit.footer, this.currentLine());
                this.nextLine();
                if (references.length) {
                    break;
                }
            }
            return true;
        }
        return false;
    }
    parseBodyAndFooter(isBody) {
        const { commit } = this;
        if (!this.isLineAvailable()) {
            return isBody;
        }
        const references = this.parseReferences(this.currentLine());
        const isStillBody = !references.length && isBody;
        if (isStillBody) {
            commit.body = appendLine(commit.body, this.currentLine());
        }
        else {
            commit.references.push(...references);
            commit.footer = appendLine(commit.footer, this.currentLine());
        }
        this.nextLine();
        return isStillBody;
    }
    parseBreakingHeader() {
        const { commit, options } = this;
        if (!options.breakingHeaderPattern || commit.notes.length || !commit.header) {
            return;
        }
        const matches = commit.header.match(options.breakingHeaderPattern);
        if (matches) {
            commit.notes.push({
                title: 'BREAKING CHANGE',
                text: matches[3]
            });
        }
    }
    parseMentions(input) {
        const { commit, regexes } = this;
        let matches;
        for (;;) {
            matches = regexes.mentions.exec(input);
            if (!matches) {
                break;
            }
            commit.mentions.push(matches[1]);
        }
    }
    parseRevert(input) {
        const { commit, options } = this;
        const correspondence = options.revertCorrespondence || [];
        const matches = options.revertPattern
            ? input.match(options.revertPattern)
            : null;
        if (matches) {
            commit.revert = correspondence.reduce((meta, key, index) => {
                meta[key] = matches[index + 1] || null;
                return meta;
            }, {});
        }
    }
    cleanupCommit() {
        const { commit } = this;
        if (commit.body) {
            commit.body = trimNewLines(commit.body);
        }
        if (commit.footer) {
            commit.footer = trimNewLines(commit.footer);
        }
        commit.notes.forEach((note) => {
            note.text = trimNewLines(note.text);
        });
    }
    /**
     * Parse commit message string into an object.
     * @param input - Commit message string.
     * @returns Commit object.
     */
    parse(input) {
        if (!input.trim()) {
            throw new TypeError('Expected a raw commit');
        }
        const commentFilter = getCommentFilter(this.options.commentChar);
        const rawLines = trimNewLines(input).split(/\r?\n/);
        const lines = truncateToScissor(rawLines).filter(line => commentFilter(line) && gpgFilter(line));
        const commit = createCommitObject();
        this.lines = lines;
        this.lineIndex = 0;
        this.commit = commit;
        const isMergeCommit = this.parseMerge();
        this.parseHeader(isMergeCommit);
        if (commit.header) {
            commit.references = this.parseReferences(commit.header);
        }
        let isBody = true;
        while (this.isLineAvailable()) {
            this.parseMeta();
            if (this.parseNotes()) {
                isBody = false;
            }
            if (!this.parseBodyAndFooter(isBody)) {
                isBody = false;
            }
        }
        this.parseBreakingHeader();
        this.parseMentions(input);
        this.parseRevert(input);
        this.cleanupCommit();
        return commit;
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiQ29tbWl0UGFyc2VyLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vc3JjL0NvbW1pdFBhcnNlci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFRQSxPQUFPLEVBQUUsZ0JBQWdCLEVBQUUsTUFBTSxZQUFZLENBQUE7QUFDN0MsT0FBTyxFQUNMLFlBQVksRUFDWixVQUFVLEVBQ1YsZ0JBQWdCLEVBQ2hCLFNBQVMsRUFDVCxpQkFBaUIsRUFDbEIsTUFBTSxZQUFZLENBQUE7QUFDbkIsT0FBTyxFQUFFLGNBQWMsRUFBRSxNQUFNLGNBQWMsQ0FBQTtBQUU3Qzs7OztHQUlHO0FBQ0gsTUFBTSxVQUFVLGtCQUFrQixDQUFDLGNBQStCLEVBQUU7SUFDbEUsa0pBQWtKO0lBQ2xKLE9BQU87UUFDTCxLQUFLLEVBQUUsSUFBSTtRQUNYLE1BQU0sRUFBRSxJQUFJO1FBQ1osTUFBTSxFQUFFLElBQUk7UUFDWixJQUFJLEVBQUUsSUFBSTtRQUNWLE1BQU0sRUFBRSxJQUFJO1FBQ1osS0FBSyxFQUFFLEVBQUU7UUFDVCxRQUFRLEVBQUUsRUFBRTtRQUNaLFVBQVUsRUFBRSxFQUFFO1FBQ2QsR0FBRyxXQUFXO0tBQ2YsQ0FBQTtBQUNILENBQUM7QUFFRDs7R0FFRztBQUNILE1BQU0sT0FBTyxZQUFZO0lBQ04sT0FBTyxDQUFlO0lBQ3RCLE9BQU8sQ0FBZTtJQUMvQixLQUFLLEdBQWEsRUFBRSxDQUFBO0lBQ3BCLFNBQVMsR0FBRyxDQUFDLENBQUE7SUFDYixNQUFNLEdBQUcsa0JBQWtCLEVBQUUsQ0FBQTtJQUVyQyxZQUFZLFVBQXlCLEVBQUU7UUFDckMsSUFBSSxDQUFDLE9BQU8sR0FBRztZQUNiLEdBQUcsY0FBYztZQUNqQixHQUFHLE9BQU87U0FDWCxDQUFBO1FBQ0QsSUFBSSxDQUFDLE9BQU8sR0FBRyxnQkFBZ0IsQ0FBQyxJQUFJLENBQUMsT0FBTyxDQUFDLENBQUE7SUFDL0MsQ0FBQztJQUVPLFdBQVc7UUFDakIsT0FBTyxJQUFJLENBQUMsS0FBSyxD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