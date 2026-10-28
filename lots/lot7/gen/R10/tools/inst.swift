import Foundation
import Vision
import CoreImage
import AppKit
// usage: inst <indir> <outdir> <x> <y>  (x,y normalisés, origine en HAUT à gauche) -> masque de la personne (instance Vision) qui contient le point,
// sinon celle dont le centre est le plus proche ; PNG gris par image d'entrée.
let a = CommandLine.arguments
let inDir = URL(fileURLWithPath: a[1]), outDir = URL(fileURLWithPath: a[2])
let px = Double(a[3])!, py = Double(a[4])!
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let files = try FileManager.default.contentsOfDirectory(atPath: inDir.path).filter { $0.hasSuffix(".png") }.sorted()
let ctx = CIContext()
for f in files {
    let url = inDir.appendingPathComponent(f)
    let req = VNGeneratePersonInstanceMaskRequest()
    let h = VNImageRequestHandler(url: url)
    try h.perform([req])
    guard let obs = req.results?.first else { print("no mask", f); continue }
    let src = CIImage(contentsOf: url)!
    let W = Int(src.extent.width), H = Int(src.extent.height)
    var best: Int = -1; var bestD = 1e9
    for idx in obs.allInstances {
        let pb = try obs.generateScaledMaskForImage(forInstances: IndexSet(integer: idx), from: h)
        CVPixelBufferLockBaseAddress(pb, .readOnly)
        let w = CVPixelBufferGetWidth(pb), hh = CVPixelBufferGetHeight(pb), rb = CVPixelBufferGetBytesPerRow(pb)
        let base = CVPixelBufferGetBaseAddress(pb)!.assumingMemoryBound(to: Float32.self)
        let fmt = CVPixelBufferGetPixelFormatType(pb)
        var sx = 0.0, sy = 0.0, n = 0.0; var hit = false
        let stride = rb / 4
        for y in Swift.stride(from: 0, to: hh, by: 4) { for x in Swift.stride(from: 0, to: w, by: 4) {
            let v = base[y * stride + x]; if v > 0.5 { sx += Double(x); sy += Double(y); n += 1 } } }
        let qx = min(w - 1, Int(px * Double(w))), qy = min(hh - 1, Int(py * Double(hh)))
        if base[qy * stride + qx] > 0.5 { hit = true }
        CVPixelBufferUnlockBaseAddress(pb, .readOnly)
        _ = fmt
        let d = hit ? -1.0 : (n > 0 ? hypot(sx / n / Double(w) - px, sy / n / Double(hh) - py) : 1e9)
        if d < bestD { bestD = d; best = idx }
    }
    if best < 0 { print("no inst", f); continue }
    let pb = try obs.generateScaledMaskForImage(forInstances: IndexSet(integer: best), from: h)
    var ci = CIImage(cvPixelBuffer: pb)
    ci = ci.transformed(by: CGAffineTransform(scaleX: CGFloat(W) / ci.extent.width, y: CGFloat(H) / ci.extent.height))
    try ctx.writePNGRepresentation(of: ci, to: outDir.appendingPathComponent(f), format: .L8, colorSpace: CGColorSpaceCreateDeviceGray())
}
print("done", files.count)
