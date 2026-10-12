// Decompile functions (and their direct non-thunk callees) to a text file.
// Script args: <outfile> <depth> <addr1> [addr2 ...]
// @category DKI

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayDeque;
import java.util.LinkedHashSet;
import java.util.Set;

public class DecompileList extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        String out = args[0];
        int maxDepth = Integer.parseInt(args[1]);
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        Set<Function> seen = new LinkedHashSet<>();
        ArrayDeque<Object[]> queue = new ArrayDeque<>();
        for (int i = 2; i < args.length; i++) {
            Address a = toAddr(args[i]);
            Function f = getFunctionAt(a);
            if (f == null) {
                f = getFunctionContaining(a);
            }
            if (f == null) {
                println("no function at " + args[i]);
                continue;
            }
            queue.add(new Object[] {f, 0});
        }
        try (PrintWriter pw = new PrintWriter(new FileWriter(out))) {
            while (!queue.isEmpty()) {
                Object[] item = queue.poll();
                Function f = (Function) item[0];
                int depth = (Integer) item[1];
                if (f.isThunk() || f.isExternal() || !seen.add(f)) {
                    continue;
                }
                DecompileResults r = ifc.decompileFunction(f, 120, new ConsoleTaskMonitor());
                pw.println("// ===== " + f.getName() + " @ " + f.getEntryPoint() + " depth=" + depth
                        + " size=" + f.getBody().getNumAddresses());
                pw.println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// FAILED " + r.getErrorMessage());
                if (depth < maxDepth) {
                    for (Function c : f.getCalledFunctions(monitor)) {
                        // skip tiny RTL helpers (Delphi System unit lives at low addresses)
                        if (c.getEntryPoint().getOffset() >= 0x00600000L) {
                            queue.add(new Object[] {c, depth + 1});
                        }
                    }
                }
            }
        }
        println("wrote " + seen.size() + " functions to " + out);
    }
}
