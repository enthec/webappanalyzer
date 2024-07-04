function preventModifications(object) {
    return new Proxy(object, {
        get(target, prop) {
            const value = target[prop];
            if (typeof value === 'object' && value !== null) {
                return preventModifications(value);
            }
            return value;
        },
        set() {
            throw new Error('Cannot modify immutable object.');
        },
        deleteProperty() {
            throw new Error('Cannot modify immutable object.');
        }
    });
}
/**
 * Apply transformation to commit.
 * @param commit
 * @param transform
 * @param context
 * @param options
 * @returns Transformed commit.
 */
export async function transformCommit(commit, transform, context, options) {
    let patch = {};
    if (typeof transform === 'function') {
        patch = await transform(preventModifications(commit), context, options);
        if (!patch) {
            return null;
        }
    }
    return {
        ...commit,
        ...patch,
        raw: commit
    };
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY29tbWl0LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vc3JjL2NvbW1pdC50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFTQSxTQUFTLG9CQUFvQixDQUFzQixNQUFTO0lBQzFELE9BQU8sSUFBSSxLQUFLLENBQUMsTUFBTSxFQUFFO1FBQ3ZCLEdBQUcsQ0FBQyxNQUFNLEVBQUUsSUFBWTtZQUN0QixNQUFNLEtBQUssR0FBRyxNQUFNLENBQUMsSUFBSSxDQUFZLENBQUE7WUFFckMsSUFBSSxPQUFPLEtBQUssS0FBSyxRQUFRLElBQUksS0FBSyxLQUFLLElBQUksRUFBRTtnQkFDL0MsT0FBTyxvQkFBb0IsQ0FBQyxLQUFLLENBQUMsQ0FBQTthQUNuQztZQUVELE9BQU8sS0FBSyxDQUFBO1FBQ2QsQ0FBQztRQUNELEdBQUc7WUFDRCxNQUFNLElBQUksS0FBSyxDQUFDLGlDQUFpQyxDQUFDLENBQUE7UUFDcEQsQ0FBQztRQUNELGNBQWM7WUFDWixNQUFNLElBQUksS0FBSyxDQUFDLGlDQUFpQyxDQUFDLENBQUE7UUFDcEQsQ0FBQztLQUNGLENBQUMsQ0FBQTtBQUNKLENBQUM7QUFFRDs7Ozs7OztHQU9HO0FBQ0gsTUFBTSxDQUFDLEtBQUssVUFBVSxlQUFlLENBQ25DLE1BQWMsRUFDZCxTQUE2RCxFQUM3RCxPQUE2QixFQUM3QixPQUE2QjtJQUU3QixJQUFJLEtBQUssR0FBMkIsRUFBRSxDQUFBO0lBRXRDLElBQUksT0FBTyxTQUFTLEtBQUssVUFBVSxFQUFFO1FBQ25DLEtBQUssR0FBRyxNQUFNLFNBQVMsQ0FBQyxvQkFBb0IsQ0FBQyxNQUFNLENBQUMsRUFBRSxPQUFPLEVBQUUsT0FBTyxDQUFDLENBQUE7UUFFdkUsSUFBSSxDQUFDLEtBQUssRUFBRTtZQUNWLE9BQU8sSUFBSSxDQUFBO1NBQ1o7S0FDRjtJQUVELE9BQU87UUFDTCxHQUFHLE1BQU07UUFDVCxHQUFHLEtBQUs7UUFDUixHQUFHLEVBQUUsTUFBTTtLQUNaLENBQUE7QUFDSCxDQUFDIn0=