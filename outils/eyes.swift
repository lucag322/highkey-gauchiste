import Foundation
import Vision
import AppKit
// usage: eyes <indir>  -> JSON {file: [[lx,ly,rx,ry, faceW], ...]} coords pixels, y vers le bas
let inDir = URL(fileURLWithPath: CommandLine.arguments[1])
let files = try FileManager.default.contentsOfDirectory(atPath: inDir.path).filter { $0.hasSuffix(".png") }.sorted()
var out: [String: [[Double]]] = [:]
for f in files {
    let url = inDir.appendingPathComponent(f)
    guard let img = NSImage(contentsOf: url), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    let W = Double(cg.width), H = Double(cg.height)
    let req = VNDetectFaceLandmarksRequest()
    try VNImageRequestHandler(cgImage: cg).perform([req])
    var faces: [[Double]] = []
    for r in req.results ?? [] {
        guard let lm = r.landmarks, let lp = lm.leftPupil, let rp = lm.rightPupil else { continue }
        let bb = r.boundingBox
        func pt(_ p: CGPoint) -> (Double, Double) {
            let x = (bb.origin.x + p.x * bb.size.width) * W
            let y = (1 - (bb.origin.y + p.y * bb.size.height)) * H
            return (x, y)
        }
        let l = pt(lp.normalizedPoints[0]), rr = pt(rp.normalizedPoints[0])
        faces.append([l.0, l.1, rr.0, rr.1, bb.size.width * W])
    }
    out[f] = faces
}
let data = try JSONSerialization.data(withJSONObject: out, options: [.sortedKeys])
FileManager.default.createFile(atPath: inDir.appendingPathComponent("eyes.json").path, contents: data)
print("done", files.count)
