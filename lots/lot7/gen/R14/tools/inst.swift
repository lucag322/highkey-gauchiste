import Foundation
import Vision
import CoreImage
import AppKit
// usage: inst <indir> <outdir> <x> <y>  (x,y normalisés, origine en HAUT à gauche) -> masque de la personne (instance Vision) qui contient le point,
// sinon celle dont le centre est le plus proche ; PNG gris par image d'entrée.
let a = CommandLine.arguments
let inDir = URL(fileURLWithPath: a[1]), outDir = URL(fileURLWithPath: a[2])
var px = Double(a[3])!, py = Double(a[4])!   // R14 : le point suit la personne choisie (centroïde de son instance) d une image à l autre
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
    var best: Int = -1; var bestD = 1e9; var cen: [Int: (Double, Double)] = [:]
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
        if n > 0 { cen[idx] = (sx / n / Double(w), sy / n / Double(hh)) }
        let d = hit ? -1.0 : (n > 0 ? hypot(sx / n / Double(w) - px, sy / n / Double(hh) - py) : 1e9)
        if d < bestD { bestD = d; best = idx }
    }
    if best < 0 { print("no inst", f); continue }
    if let c = cen[best] { px = 0.5 * px + 0.5 * c.0; py = 0.5 * py + 0.5 * c.1 }
    let pb = try obs.generateScaledMaskForImage(forInstances: IndexSet(integer: best), from: h)
    // R14 : chaque pixel va à l'instance la plus forte (sinon une tête derrière lui est comptée dans son masque)
    let others = obs.allInstances.filter { $0 != best }
    if !others.isEmpty {
        CVPixelBufferLockBaseAddress(pb, [])
        let w = CVPixelBufferGetWidth(pb), hh = CVPixelBufferGetHeight(pb), st = CVPixelBufferGetBytesPerRow(pb) / 4
        let bb = CVPixelBufferGetBaseAddress(pb)!.assumingMemoryBound(to: Float32.self)
        for o in others {
            let po = try obs.generateScaledMaskForImage(forInstances: IndexSet(integer: o), from: h)
            CVPixelBufferLockBaseAddress(po, .readOnly)
            let so = CVPixelBufferGetBytesPerRow(po) / 4
            let ob = CVPixelBufferGetBaseAddress(po)!.assumingMemoryBound(to: Float32.self)
            for y in 0..<hh { for x in 0..<w {
                let v = ob[y * so + x]; let b = bb[y * st + x]
                if v > 0.3 && v >= b * 0.8 { bb[y * st + x] = max(0, b - v) }
            } }
            CVPixelBufferUnlockBaseAddress(po, .readOnly)
        }
        CVPixelBufferUnlockBaseAddress(pb, [])
    }
    var ci = CIImage(cvPixelBuffer: pb)
    ci = ci.transformed(by: CGAffineTransform(scaleX: CGFloat(W) / ci.extent.width, y: CGFloat(H) / ci.extent.height))
    try ctx.writePNGRepresentation(of: ci, to: outDir.appendingPathComponent(f), format: .L8, colorSpace: CGColorSpaceCreateDeviceGray())
}
print("done", files.count)
