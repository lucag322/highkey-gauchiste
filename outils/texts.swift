import Foundation
import Vision
import AppKit
// usage: texts <indir> -> <indir>/texts.json {fichier: [[x,y,w,h,"texte"], ...]} en fractions, y vers le BAS
let inDir = URL(fileURLWithPath: CommandLine.arguments[1])
let files = try FileManager.default.contentsOfDirectory(atPath: inDir.path).filter { $0.hasSuffix(".jpg") || $0.hasSuffix(".png") }.sorted()
var out: [String: [[Any]]] = [:]
for f in files {
    let url = inDir.appendingPathComponent(f)
    guard let img = NSImage(contentsOf: url), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["fr-FR", "en-US"]
    try? VNImageRequestHandler(cgImage: cg).perform([req])
    out[f] = (req.results ?? []).compactMap { r in
        guard let t = r.topCandidates(1).first, t.confidence > 0.4 else { return nil }
        let b = r.boundingBox
        return [Double(b.origin.x), Double(1 - b.origin.y - b.size.height), Double(b.size.width), Double(b.size.height), t.string]
    }
}
let data = try JSONSerialization.data(withJSONObject: out, options: [.sortedKeys])
FileManager.default.createFile(atPath: inDir.appendingPathComponent("texts.json").path, contents: data)
print("texts", files.count)
