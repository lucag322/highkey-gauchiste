import Foundation
import Vision
import CoreImage
import AppKit
// usage: segment <indir> <outdir>  -> writes grayscale mask PNG per input PNG
let args = CommandLine.arguments
let inDir = URL(fileURLWithPath: args[1]), outDir = URL(fileURLWithPath: args[2])
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let files = try FileManager.default.contentsOfDirectory(atPath: inDir.path).filter { $0.hasSuffix(".png") }.sorted()
let ctx = CIContext()
for f in files {
    let url = inDir.appendingPathComponent(f)
    let req = VNGeneratePersonSegmentationRequest()
    req.qualityLevel = .accurate
    req.outputPixelFormat = kCVPixelFormatType_OneComponent8
    let h = VNImageRequestHandler(url: url)
    try h.perform([req])
    guard let pb = req.results?.first?.pixelBuffer else { print("no mask", f); continue }
    var ci = CIImage(cvPixelBuffer: pb)
    let src = CIImage(contentsOf: url)!
    let sx = src.extent.width / ci.extent.width, sy = src.extent.height / ci.extent.height
    ci = ci.transformed(by: CGAffineTransform(scaleX: sx, y: sy))
    let cs = CGColorSpaceCreateDeviceGray()
    try ctx.writePNGRepresentation(of: ci, to: outDir.appendingPathComponent(f), format: .L8, colorSpace: cs)
}
print("done", files.count)
