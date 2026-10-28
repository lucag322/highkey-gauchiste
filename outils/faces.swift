import Foundation
import Vision
import AppKit
// usage: faces <indir> -> <indir>/faces.json {fichier: [[x,y,w,h], ...]} en fractions, y vers le BAS
let inDir = URL(fileURLWithPath: CommandLine.arguments[1])
let files = try FileManager.default.contentsOfDirectory(atPath: inDir.path).filter { $0.hasSuffix(".jpg") || $0.hasSuffix(".png") }.sorted()
var out: [String: [[Double]]] = [:]
for f in files {
    let url = inDir.appendingPathComponent(f)
    guard let img = NSImage(contentsOf: url), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    let req = VNDetectFaceRectanglesRequest()
    try? VNImageRequestHandler(cgImage: cg).perform([req])
    out[f] = (req.results ?? []).map { r in
        let b = r.boundingBox
        return [Double(b.origin.x), Double(1 - b.origin.y - b.size.height), Double(b.size.width), Double(b.size.height)]
    }
}
let data = try JSONSerialization.data(withJSONObject: out, options: [.sortedKeys])
FileManager.default.createFile(atPath: inDir.appendingPathComponent("faces.json").path, contents: data)
print("faces", files.count)
